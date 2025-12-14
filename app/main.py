from flask import Flask
from flask import request
import logging

from models import db, add_sample_data, init_db

class Config:
    SECRET_KEY = 'super-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///timetable.db'
    # SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:admin123@localhost:5432/timetable'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

logging.basicConfig(level=logging.INFO)

def init_routes(app: Flask):
    """
    Инициализация всех маршрутов приложения
    """
    from routes.auth import auth_bp
    from routes.moodle import moodle_bp
    from routes.bookings import booking_bp
    from routes.classrooms import classroom_bp

    @app.before_request
    def log_request():
        """Логирование информации о запросе перед его обработкой"""
        app.logger.info(f"Request: {request.method} {request.url}") 

    app.register_blueprint(auth_bp)
    app.register_blueprint(moodle_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(classroom_bp)

    @app.route('/')
    def helloworld():
        return "hello from schedule app"

def create_app():

    app = Flask(__name__)
    app.config.from_object(Config)

    # Инициализация расширений
    db.init_app(app)

    # Инициализация базы данных
    with app.app_context():
        init_db()  # Используем функцию с проверкой существования таблиц

        # Раскомментировать следующую строку для добавления тестовых данных при первом запуске
        add_sample_data()  # РАСКОММЕНТИРОВАНО для добавления тестовых данных

    init_routes(app)

    return app
app = create_app()

def main():
    """Главная функция запуска приложения"""

    print("Запуск University Management System...")
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)


if __name__ == '__main__':
    main()