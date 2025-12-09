"""
Модели базы данных для University Management System
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Numeric

# Инициализируем экземпляр SQLAlchemy
db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    notifications = db.relationship('Notification', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.id}: {self.role}>'


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(50), nullable=False, default='info')

    def __repr__(self):
        return f'<Notification {self.id}>'


class Classroom(db.Model):
    __tablename__ = 'classrooms'

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20))
    eios_id =db.Column(db.Integer)
    equipment = db.Column(db.Text)
    capacity = db.Column(db.Integer)
    description = db.Column(db.Text)
    schedules = db.relationship('Schedule', backref='classroom', lazy=True)
    bookings = db.relationship('Booking', backref='classroom', lazy=True)
    pricing = db.relationship('Pricing', backref='classroom', lazy=True, uselist=False)

    def __repr__(self):
        return f'<Classroom {self.number}>'


class Pricing(db.Model):
    __tablename__ = 'pricing'

    id = db.Column(db.Integer, primary_key=True)
    classroom_number = db.Column(db.String(20), db.ForeignKey('classrooms.id'), nullable=False, unique=True)
    price_per_hour = db.Column(db.Numeric(10, 2), nullable=False)  # цена за час

    def __repr__(self):
        return f'<Pricing {self.classroom_number}: {self.price_per_hour}>'


class Schedule(db.Model):
    __tablename__ = 'schedules'

    id = db.Column(db.Integer, primary_key=True)
    classroom_number = db.Column(db.String(20), db.ForeignKey('classrooms.id'), nullable=False)
    lesson = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Schedule {self.id}: {self.lesson}>'


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    classroom_number = db.Column(db.String(20), db.ForeignKey('classrooms.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.Boolean, default=None)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    total_cost = db.Column(db.Numeric(10, 2))  # общая стоимость бронирования

    def __repr__(self):
        return f'<Booking {self.id}>'


def init_db():
    """Инициализация базы данных - создание всех таблиц"""
    from sqlalchemy import inspect

    # Создаем инспектор для проверки существования таблиц
    inspector = inspect(db.engine)
    existing_tables = inspector.get_table_names()

    # Проверяем, есть ли уже наши таблицы
    required_tables = ['users', 'classrooms', 'schedules', 'bookings', 'notifications', 'pricing']
    tables_exist = all(table in existing_tables for table in required_tables)

    if not tables_exist:
        db.create_all()
        print("✅ Все таблицы успешно созданы в PostgreSQL!")
    else:
        print("✅ Таблицы уже существуют в базе данных")


def add_sample_data():
    """Добавление тестовых данных в базу"""
    try:
        # Очищаем существующие данные (опционально)
        db.session.query(Pricing).delete()
        db.session.query(Booking).delete()
        db.session.query(Schedule).delete()
        db.session.query(Classroom).delete()
        db.session.query(User).delete()
        db.session.query(Notification).delete()

        # Создаем тестовые аудитории
        classrooms = [
            Classroom(
                number="101",
                equipment="Проектор, маркерная доска, кондиционер",
                capacity=30,
                description="Аудитория для лекций и семинаров"
            ),
            Classroom(
                number="201",
                equipment="Компьютеры, проектор, интерактивная доска",
                capacity=25,
                description="Компьютерный класс"
            ),
            Classroom(
                number="301",
                equipment="Мультимедийная система, микрофоны",
                capacity=50,
                description="Конференц-зал"
            ),
            Classroom(
                number="102",
                equipment="Маркерная доска",
                capacity=20,
                description="Малая аудитория"
            )
        ]

        # Создаем тестовых пользователей
        users = [
            User(role="преподаватель", email="teacher@university.edu"),
            User(role="студент", email="student@university.edu"),
            User(role="администратор", email="admin1@university.edu"),
            User(role="администратор", email="admin2@university.edu")
        ]

        # Добавляем цены для аудиторий
        pricing = [
            Pricing(classroom_number="101", price_per_hour=1500.00),
            Pricing(classroom_number="201", price_per_hour=2000.00),
            Pricing(classroom_number="301", price_per_hour=3000.00),
            Pricing(classroom_number="102", price_per_hour=1000.00)
        ]

        # Добавляем тестовые бронирования
        from datetime import datetime, timedelta
        bookings = [
            Booking(
                classroom_number="101",
                date=datetime.now() - timedelta(days=5),
                duration=3,
                description="Лекция по математике",
                user_id=1,
                status='approved',
                total_cost=4500.00  # 1500 * 3
            ),
            Booking(
                classroom_number="201",
                date=datetime.now() - timedelta(days=3),
                duration=2,
                description="Практика по программированию",
                user_id=1,
                status='approved',
                total_cost=4000.00  # 2000 * 2
            ),
            Booking(
                classroom_number="301",
                date=datetime.now() - timedelta(days=2),
                duration=4,
                description="Конференция",
                user_id=2,
                status='approved',
                total_cost=12000.00  # 3000 * 4
            ),
            Booking(
                classroom_number="101",
                date=datetime.now() - timedelta(days=1),
                duration=2,
                description="Семинар",
                user_id=1,
                status='approved',
                total_cost=3000.00  # 1500 * 2
            ),
            Booking(
                classroom_number="201",
                date=datetime.now(),
                duration=3,
                description="Лабораторная работа",
                user_id=2,
                status='approved',
                total_cost=6000.00  # 2000 * 3
            )
        ]

        # Добавляем все в сессию
        db.session.add_all(classrooms)
        db.session.add_all(users)
        db.session.add_all(pricing)
        db.session.add_all(bookings)
        db.session.commit()

        print("✅ Тестовые данные успешно добавлены!")

    except Exception as e:
        db.session.rollback()
        print(f"❌ Ошибка при добавлении тестовых данных: {e}")