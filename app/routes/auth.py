from datetime import datetime, timedelta,timezone
from functools import wraps
from flask import Blueprint, request, jsonify, current_app, g
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

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", None)
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header.split(" ")[1]
        payload = decode_token(token)

        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Сохраняем user_id для использования внутри маршрута
        g.user_id = payload["sub"]
        return f(*args, **kwargs)
    return decorated

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'message': 'Email and password required'}), 400
    email = data['email'].lower().strip()
    password = data['password']

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

@auth_bp.route('/access', methods=['POST'])
def login():
    current_app.logger.debug("попытка авторизации")
    data = request.get_json()
    current_app.logger.debug(data)
    current_app.logger.debug(data['email'])
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'message': 'Email and password required'}), 400

    user = User.query.filter_by(email=data['email']).first()
    current_app.logger.debug(user)
    current_app.logger.debug("3")
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
    current_app.logger.debug("4")
    access = create_access_token(user)
    refresh = create_refresh_token(user)
    current_app.logger.debug("5")
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