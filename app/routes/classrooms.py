from flask import Blueprint,jsonify 
from http import HTTPStatus
import json, os
from sqlalchemy import func

from extensions import db
from models import Classroom, Booking

classroom_bp = Blueprint('classroom', __name__, url_prefix='/classroom')

LESSONS_PATH="events/lessons"
@classroom_bp.route('/schedule/<int:aud_id>', methods=['POST'])
def get_schedule(aud_id):
        # 1. Ищем аудиторию
        classroom = Classroom.query.get(aud_id)
        if not classroom:
            return jsonify({"error": "Аудитория не найдена"}), HTTPStatus.NOT_FOUND

        # 2. Загружаем бронирования из БД (только подтверждённые)
        bookings = Booking.query.filter_by(
            classroom_id=classroom.id,
            status=True
        ).all()

        # 3. Преобразуем бронирования в формат FullCalendar
        booking_events = []
        for b in bookings:
            event = {
                "title": b.description or "Бронирование",
                "start": b.date_start.isoformat(),
                "end": b.date_end.isoformat(),
                "extendedProps": {
                    "booking_id": b.id,
                    "user_id": b.user_id
                }
            }
            booking_events.append(event)

        # 4. Загружаем внешние JSON события
        events_path = os.path.join(LESSONS_PATH, f"{classroom.eios_id}.json")
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

@classroom_bp.route('/statistics')
def top_profitable_classrooms():
    """Статистика самых прибыльных аудиторий"""
    try:
        # Агрегируем данные: группируем по аудитории, суммируем общую выручку
        stats = db.session.query(
            Classroom.number,
            Classroom.description,
            Classroom.capacity,
            Classroom.price,
            func.sum(Booking.total_cost).label('total_revenue'),
            func.count(Booking.id).label('booking_count'),
            func.avg(Booking.get_duration()).label('avg_duration')
        ).join(
            Booking, Classroom.id == Booking.classroom_id
        ).filter(
            Booking.status == 'approved'  # Учитываем только подтвержденные бронирования
        ).group_by(
            Classroom.number, Classroom.description, Classroom.capacity, 
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