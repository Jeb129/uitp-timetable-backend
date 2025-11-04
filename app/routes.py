"""
Маршруты API для University Management System
"""
from flask import jsonify
from models import Classroom, User, Schedule, Booking, db


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
                    'role': u.role
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
                    'description': b.description
                } for b in bookings
            ]
        })

    @app.route('/health')
    def health_check():
        """Проверка здоровья приложения"""
        return jsonify({
            "status": "healthy",
            "database": "connected"  # Можно добавить проверку подключения к БД
        })