from flask import Flask
from models import db, add_sample_data, init_db
from routes import init_routes


def create_app():
    app = Flask(__name__)

    # Конфигурация приложения
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin123@localhost:5432/timetable'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Инициализация расширений
    db.init_app(app)

    # Инициализация базы данных
    with app.app_context():
        init_db()  # Используем функцию с проверкой существования таблиц

        # Раскомментировать следующую строку для добавления тестовых данных при первом запуске
        # add_sample_data()

    # Регистрация маршрутов
    init_routes(app)

    return app


def main():
    """Главная функция запуска приложения"""
    app = create_app()

    print("Запуск University Management System...")
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)


if __name__ == '__main__':
    main()