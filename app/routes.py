"""
Маршруты API для University Management System
"""
from flask import jsonify, request
from models import Classroom, User, Schedule, Booking, Notification, db
from email_service import email_service
from datetime import datetime


def init_routes(app):
    """
    Инициализация всех маршрутов приложения
    """

    @app.route('/')
    def index():
        return jsonify({
            "message": "University Management System API",
            "version": "1.0",
            "endpoints": {
                "classrooms": "/classrooms",
                "users": "/users",
                "schedules": "/schedules",
                "bookings": "/bookings"
            }
        })

    @app.route('/classrooms')
    def list_classrooms():
        """Получить список всех аудиторий"""
        classrooms = Classroom.query.all()
        return jsonify({
            'classrooms': [
                {
                    'number': c.number,
                    'equipment': c.equipment,
                    'capacity': c.capacity,
                    'description': c.description
                } for c in classrooms
            ]
        })

    @app.route('/users')
    def list_users():
        """Получить список всех пользователей"""
        users = User.query.all()
        return jsonify({
            'users': [
                {
                    'id': u.id,
                    'role': u.role,
                    'email': u.email
                } for u in users
            ]
        })

    @app.route('/schedules')
    def list_schedules():
        """Получить расписание"""
        schedules = Schedule.query.all()
        return jsonify({
            'schedules': [
                {
                    'id': s.id,
                    'classroom': s.classroom_number,
                    'lesson': s.lesson,
                    'date': s.date.isoformat() if s.date else None
                } for s in schedules
            ]
        })

    @app.route('/bookings')
    def list_bookings():
        """Получить список бронирований"""
        bookings = Booking.query.all()
        return jsonify({
            'bookings': [
                {
                    'id': b.id,
                    'classroom': b.classroom_number,
                    'date': b.date.isoformat() if b.date else None,
                    'duration': b.duration,
                    'description': b.description,
                    'user_id': b.user_id,
                    'status': b.status
                } for b in bookings
            ]
        })

    @app.route('/bookings', methods=['POST'])
    def create_booking():
        """Создание нового бронирования"""
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

            # Создаем бронирование
            new_booking = Booking(
                classroom_number=data['classroom_number'],
                date=datetime.fromisoformat(data['date'].replace('Z', '+00:00')),
                duration=data['duration'],
                description=data.get('description', ''),
                user_id=data['user_id'],
                status='pending'
            )

            db.session.add(new_booking)
            db.session.commit()

            # Подготавливаем данные для уведомлений
            booking_data = {
                'classroom_number': data['classroom_number'],
                'date': data['date'],
                'duration': data['duration'],
                'description': data.get('description', ''),
                'user_email': user.email
            }

            # Создаем уведомления для администраторов
            admin_users = User.query.filter_by(role='администратор').all()
            admin_emails = [admin.email for admin in admin_users]

            # Отправляем email администраторам
            email_service.send_booking_notification_to_admins(booking_data, admin_emails)

            # Создаем записи уведомлений для администраторов
            for admin in admin_users:
                admin_notification = Notification(
                    user_id=admin.id,
                    message=f"Новая заявка на бронирование аудитории {data['classroom_number']} от пользователя {user.email}",
                    type='booking_request'
                )
                db.session.add(admin_notification)

            # Отправляем email пользователю
            email_service.send_booking_confirmation_to_user(user.email, booking_data)

            # Создаем уведомление для пользователя
            user_notification = Notification(
                user_id=user.id,
                message=f"Ваша заявка на бронирование аудитории {data['classroom_number']} принята в рассмотрение",
                type='booking_confirmation'
            )
            db.session.add(user_notification)

            db.session.commit()

            return jsonify({
                'message': 'Booking created successfully',
                'booking_id': new_booking.id,
                'status': new_booking.status
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Failed to create booking: {str(e)}'}), 500

    @app.route('/bookings/<int:booking_id>/approve', methods=['POST'])
    def approve_booking(booking_id):
        """Подтверждение бронирования администратором"""
        try:
            booking = Booking.query.get(booking_id)
            if not booking:
                return jsonify({'error': 'Booking not found'}), 404

            booking.status = 'approved'

            # Создаем уведомление для пользователя
            user_notification = Notification(
                user_id=booking.user_id,
                message=f"Ваша заявка на бронирование аудитории {booking.classroom_number} подтверждена",
                type='booking_approved'
            )
            db.session.add(user_notification)

            db.session.commit()

            return jsonify({'message': 'Booking approved successfully'}), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Failed to approve booking: {str(e)}'}), 500

    @app.route('/bookings/<int:booking_id>/reject', methods=['POST'])
    def reject_booking(booking_id):
        """Отклонение бронирования администратором"""
        try:
            booking = Booking.query.get(booking_id)
            if not booking:
                return jsonify({'error': 'Booking not found'}), 404

            booking.status = 'rejected'

            # Создаем уведомление для пользователя
            user_notification = Notification(
                user_id=booking.user_id,
                message=f"Ваша заявка на бронирование аудитории {booking.classroom_number} отклонена",
                type='booking_rejected'
            )
            db.session.add(user_notification)

            db.session.commit()

            return jsonify({'message': 'Booking rejected successfully'}), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Failed to reject booking: {str(e)}'}), 500

    @app.route('/notifications')
    def list_notifications():
        """Получить список уведомлений"""
        notifications = Notification.query.all()
        return jsonify({
            'notifications': [
                {
                    'id': n.id,
                    'user_id': n.user_id,
                    'message': n.message,
                    'type': n.type,
                    'created_at': n.created_at.isoformat() if n.created_at else None
                } for n in notifications
            ]
        })

    @app.route('/health')
    def health_check():
        """Проверка здоровья приложения"""
        return jsonify({
            "status": "healthy",
            "database": "connected"
        })