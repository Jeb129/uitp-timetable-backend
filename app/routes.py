"""
Маршруты API для University Management System
"""
import os
import json
from flask import jsonify, request
from http import HTTPStatus
import requests
from models import Classroom, User, Schedule, Booking, Notification, Pricing, db
from email_service import email_service
from datetime import datetime, timedelta
from sqlalchemy import func


def init_routes(app):
    """
    Инициализация всех маршрутов приложения
    """

    @app.route('/statistics/top_profitable_classrooms')
    def top_profitable_classrooms():
        """Статистика самых прибыльных аудиторий"""
        try:
            # Агрегируем данные: группируем по аудитории, суммируем общую выручку
            stats = db.session.query(
                Classroom.number,
                Classroom.description,
                Classroom.capacity,
                Pricing.price_per_hour,
                func.sum(Booking.total_cost).label('total_revenue'),
                func.count(Booking.id).label('booking_count'),
                func.avg(Booking.duration).label('avg_duration')
            ).join(
                Pricing, Classroom.number == Pricing.classroom_number
            ).join(
                Booking, Classroom.number == Booking.classroom_number
            ).filter(
                Booking.status == 'approved'  # Учитываем только подтвержденные бронирования
            ).group_by(
                Classroom.number, Classroom.description, Classroom.capacity, Pricing.price_per_hour
            ).order_by(
                func.sum(Booking.total_cost).desc()  # Сортируем по убыванию выручки
            ).all()

            # Форматируем результат для JSON
            result = []
            for stat in stats:
                result.append({
                    'classroom_number': stat.number,
                    'description': stat.description,
                    'capacity': stat.capacity,
                    'price_per_hour': float(stat.price_per_hour) if stat.price_per_hour else 0,
                    'total_revenue': float(stat.total_revenue) if stat.total_revenue else 0,
                    'booking_count': stat.booking_count,
                    'avg_duration': float(stat.avg_duration) if stat.avg_duration else 0,
                    'revenue_per_booking': float(stat.total_revenue) / stat.booking_count if stat.booking_count else 0
                })

            return jsonify({
                'success': True,
                'statistics': {
                    'top_profitable_classrooms': result,
                    'total_revenue_all': sum(item['total_revenue'] for item in result),
                    'total_bookings_all': sum(item['booking_count'] for item in result)
                }
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to calculate statistics: {str(e)}'
            }), 500

    @app.route('/pricing')
    def list_pricing():
        """Получить список цен для аудиторий"""
        pricing = Pricing.query.all()
        return jsonify({
            'pricing': [
                {
                    'id': p.id,
                    'classroom_number': p.classroom_number,
                    'price_per_hour': float(p.price_per_hour) if p.price_per_hour else 0
                } for p in pricing
            ]
        })

    # Обновляем создание бронирования для автоматического расчета стоимости
    @app.route('/bookings', methods=['POST'])
    def create_booking():
        """Создание нового бронирования с автоматическим расчетом стоимости"""
        try:
            data = request.get_json()

            # Проверяем обязательные поля
            required_fields = ['classroom_number', 'date', 'duration', 'user_id']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400

            # Проверяем существование пользователя
            user = User.query.get(data['user_id'])
            if not user:
                return jsonify({'error': 'User not found'}), 404

            # Проверяем существование аудитории
            classroom = Classroom.query.get(data['classroom_number'])
            if not classroom:
                return jsonify({'error': 'Classroom not found'}), 404

            # Получаем цену за аудиторию
            pricing = Pricing.query.filter_by(classroom_number=data['classroom_number']).first()
            if not pricing:
                return jsonify({'error': 'Pricing not found for this classroom'}), 400

            # Рассчитываем общую стоимость
            total_cost = pricing.price_per_hour * data['duration']

            # Создаем бронирование
            new_booking = Booking(
                classroom_number=data['classroom_number'],
                date=datetime.fromisoformat(data['date'].replace('Z', '+00:00')),
                duration=data['duration'],
                description=data.get('description', ''),
                user_id=data['user_id'],
                status='pending',
                total_cost=total_cost
            )

            db.session.add(new_booking)
            db.session.commit()

            # ... остальной код создания бронирования (уведомления, emails) ...

            return jsonify({
                'message': 'Booking created successfully',
                'booking_id': new_booking.id,
                'status': new_booking.status,
                'total_cost': float(total_cost)
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Failed to create booking: {str(e)}'}), 500
   
    MOODLE_URL = "http://localhost:5002/webservice/rest/server.php" # Тут апи сдо должно быть но пока что локальное (кто хочет - ставьте сервер мудла себе сами.)
    MOODLE_TOKEN = "YOUR_MOODLE_TOKEN" # Аналогично предыдущему пункту нужен  токен от сдо с правами moodle/user:viewdetails.
    WS_FUNCTION = "core_user_get_users" # имя метода
    @app.route("/moodle/user")
    def get_moodle_user():
        email = request.args.get("email")

        if not email:
            return jsonify({"error": "email parameter is required"}), 400

        params = {
            "wstoken": MOODLE_TOKEN,
            "wsfunction": WS_FUNCTION,
            "moodlewsrestformat": "json",
            "criteria[0][key]": "email",
            "criteria[0][value]": email,
        }

        try:
            response = requests.get(MOODLE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            return jsonify({"error": str(e)}), 502

        return jsonify(data)

    @app.route("/bookings/update", methods = ['POST'])
    def change_boocking_status():
        data = request.get_json()
        id = data['id']
        status = data["status"] #Булево
        comment = data["comment"]

        booking = Booking.query.get(id)
        if not booking:
            return HTTPStatus.BAD_GATEWAY
                
        booking.status = status

        notification = Notification(user_id = booking.user_id, message = f"Заявка № {id} {"одобрена" if status else "отклонена"}.\n Комментарий модерации: {comment}")
        db.session.add(notification)

        db.session.commit()

    @app.route('/schedule/<int:aud_id>')
    def get_schedule(aud_id):
        # 1. Ищем аудиторию
        classroom = Classroom.query.get(aud_id)
        if not classroom:
            return jsonify({"error": "Аудитория не найдена"}), HTTPStatus.NOT_FOUND

        # 2. Загружаем бронирования из БД (только подтверждённые)
        bookings = Booking.query.filter_by(
            classroom_number=classroom.id,
            status=True
        ).all()

        # 3. Преобразуем бронирования в формат FullCalendar
        booking_events = []
        for b in bookings:
            event = {
                "title": b.description or "Бронирование",
                "start": b.date.isoformat(),
                "end": (b.date + timedelta(minutes=b.duration)).isoformat(),
                "extendedProps": {
                    "booking_id": b.id,
                    "user_id": b.user_id
                }
            }
            booking_events.append(event)

        # 4. Загружаем внешние JSON события
        events_path = os.path.join("events", f"{classroom.eios_id}.json")
        external_events = []

        if os.path.exists(events_path):
            with open(events_path, encoding='utf-8') as f:
                try:
                    external_events = json.load(f)
                except Exception:
                    external_events = []  # на случай плохого JSON

        # 5. Объединяем
        all_events = external_events + booking_events

        return jsonify(all_events), HTTPStatus.OK