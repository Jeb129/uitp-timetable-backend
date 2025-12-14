from datetime import datetime
from flask import Blueprint, request, jsonify
from http import HTTPStatus

from extensions import db
from models import Classroom, Booking, User, Notification

booking_bp = Blueprint('booking', __name__, url_prefix='/booking')

@booking_bp.route("/search",methods=["GET"])
def get_booking():
    key = request.args.get("key")
    value = request.args.get("value")
    try:
        query = Booking.query
        if not (key is None or value is None):
            query = query.filter(getattr(Booking, key) == value)
        bookings = query.all()
        return jsonify([b.to_dict() for b in bookings])
    
    except Exception as e:
        return jsonify({"error": f"{e}"}), HTTPStatus.INTERNAL_SERVER_ERROR       

@booking_bp.route("/create",methods=["POST"])
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

            # Рассчитываем общую стоимость
            # Создаем бронирование
            new_booking = Booking(
                classroom_number=data['classroom_number'],
                date=datetime.fromisoformat(data['date'].replace('Z', '+00:00')),
                duration=data['duration'],
                description=data.get('description', ''),
                user_id=data['user_id'],
                status='pending',
                total_cost=1000
            )

            db.session.add(new_booking)
            db.session.commit()

            # ... остальной код создания бронирования (уведомления, emails) ...

            return jsonify({
                'message': 'Booking created successfully',
                'booking_id': new_booking.id,
                'status': new_booking.status,
                'total_cost': float(1000)
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Failed to create booking: {str(e)}'}), 500


@booking_bp.route("/update", methods = ['POST'])
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

