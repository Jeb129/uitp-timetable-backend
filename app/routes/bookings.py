from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
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
            current_app.logger.debug(1)
            data = request.get_json()

            # Проверяем обязательные поля
            required_fields = ['classroom_id', 'date_start', 'date_end', 'duration', 'user_id']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            current_app.logger.debug(2)
            # Проверяем существование пользователя
            user = User.query.get(data['user_id'])
            if not user:
                return jsonify({'error': 'User not found'}), 404
            current_app.logger.debug(3)
            # Проверяем существование аудитории
            classroom = Classroom.query.get(data['classroom_id'])
            if not classroom:
                return jsonify({'error': 'Classroom not found'}), 404
            current_app.logger.debug(4)
            # Получаем цену за аудиторию
            date_s=datetime.fromisoformat(data['date_start'].replace('Z', '+00:00'))
            date_e=datetime.fromisoformat(data['date_end'].replace('Z', '+00:00'))
            current_app.logger.debug(5)
            new_booking = Booking(
                user_id=data['user_id'],
                classroom_id=data['classroom_id'],
                date_start=date_s,
                date_end=date_e,
                description=data.get('description', ''),
                total_cost=classroom.get_cost((date_e-date_s).total_seconds()/3600)
            )
            
            db.session.add(new_booking)
            db.session.commit()
            

            return jsonify({
                'message': 'Booking created successfully',
                'booking_id': new_booking.id,
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

