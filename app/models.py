"""
Модели базы данных для University Management System
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Инициализируем экземпляр SQLAlchemy
db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(50), nullable=False)
    notifications = db.relationship('Notification', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.id}: {self.role}>'


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Notification {self.id}>'


class Classroom(db.Model):
    __tablename__ = 'classrooms'

    number = db.Column(db.String(20), primary_key=True)
    equipment = db.Column(db.Text)
    capacity = db.Column(db.Integer)
    description = db.Column(db.Text)
    schedules = db.relationship('Schedule', backref='classroom', lazy=True)
    bookings = db.relationship('Booking', backref='classroom', lazy=True)

    def __repr__(self):
        return f'<Classroom {self.number}>'


class Schedule(db.Model):
    __tablename__ = 'schedules'

    id = db.Column(db.Integer, primary_key=True)
    classroom_number = db.Column(db.String(20), db.ForeignKey('classrooms.number'), nullable=False)
    lesson = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Schedule {self.id}: {self.lesson}>'


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    classroom_number = db.Column(db.String(20), db.ForeignKey('classrooms.number'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)

    def __repr__(self):
        return f'<Booking {self.id}>'


def init_db():
    """Инициализация базы данных - создание всех таблиц"""
    from sqlalchemy import inspect

    # Создаем инспектор для проверки существования таблиц
    inspector = inspect(db.engine)
    existing_tables = inspector.get_table_names()

    # Проверяем, есть ли уже наши таблицы
    required_tables = ['users', 'classrooms', 'schedules', 'bookings', 'notifications']
    tables_exist = all(table in existing_tables for table in required_tables)

    if not tables_exist:
        db.create_all()
        print("✅ Все таблицы успешно созданы в PostgreSQL!")
    else:
        print("✅ Таблицы уже существуют в базе данных")


def add_sample_data():
    """Добавление тестовых данных в базу"""
    try:
        # Создаем тестовые аудитории
        classroom1 = Classroom(
            number="101",
            equipment="Проектор, маркерная доска, кондиционер",
            capacity=30,
            description="Аудитория для лекций и семинаров"
        )

        classroom2 = Classroom(
            number="201",
            equipment="Компьютеры, проектор, интерактивная доска",
            capacity=25,
            description="Компьютерный класс"
        )

        # Создаем тестовых пользователей
        teacher = User(role="преподаватель")
        student = User(role="студент")
        admin = User(role="администратор")

        # Добавляем все в сессию
        db.session.add_all([classroom1, classroom2, teacher, student, admin])
        db.session.commit()

        print("✅ Тестовые данные успешно добавлены!")

    except Exception as e:
        db.session.rollback()
        print(f"❌ Ошибка при добавлении тестовых данных: {e}")