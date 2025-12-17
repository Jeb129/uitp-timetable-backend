from datetime import datetime, timedelta,timezone
from flask import Blueprint, request, jsonify, current_app
import jwt

from extensions import db
from models import User

# Путь начинается с localhost:8000/auth/
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# вспомогательные функции
def create_access_token(user):
    payload = {
        'user_id': user.id,
        'role': user.role,
        'exp': datetime.now(timezone.utc) + timedelta(minutes=30),
        'type': 'access'
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
def create_refresh_token(user):
    payload = {
        'user_id': user.id,
        'exp': datetime.now(timezone.utc) + timedelta(days=7),
        'type': 'refresh'
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
def decode_token(token):
    return jwt.decode(
        token,
        current_app.config['SECRET_KEY'],
        algorithms=['HS256']
    )
#
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'message': 'Email and password required'}), 400

    email = data['email'].lower().strip()
    password = data['password']

    if len(password) < 6:
        return jsonify({'message': 'Password must be at least 6 characters'}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'message': 'User already exists'}), 409

    user = User(
        email=email,
        role='user',
        confirmed=False
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({
        'message': 'User registered successfully'
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'message': 'Email and password required'}), 400

    user = User.query.filter_by(email=data['email']).first()

    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401

    access = create_access_token(user)
    refresh = create_refresh_token(user)

    return jsonify({
        'access': access,
        'refresh': refresh
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    data = request.get_json()

    if not data or 'refresh' not in data:
        return jsonify({'message': 'Refresh token required'}), 400

    try:
        payload = decode_token(data['refresh'])

        if payload.get('type') != 'refresh':
            return jsonify({'message': 'Invalid token type'}), 401

        user = User.query.get(payload['user_id'])
        if not user:
            return jsonify({'message': 'User not found'}), 401

        new_access = create_access_token(user)
        return jsonify({'access': new_access}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Refresh token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid refresh token'}), 401