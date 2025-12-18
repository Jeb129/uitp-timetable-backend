from flask import Blueprint, request, jsonify
from models import User
import requests
from extensions import db

MOODLE_URL = "http://localhost:8080/webservice/rest/server.php" # Тут апи сдо должно быть но пока что локальное (кто хочет - ставьте сервер мудла себе сами.)
MOODLE_TOKEN = "4137a05f4dd45307d408c29bb00a8189" # Аналогично предыдущему пункту нужен  токен от сдо с правами moodle/user:viewdetails.
WS_FUNCTION = "core_user_get_users" # имя метода

moodle_bp = Blueprint('moodle', __name__, url_prefix='/moodle')

@moodle_bp.route("/user",methods=['GET'])
def get_moodle_user():
    email = request.args.get("email")

    if not email:
        return jsonify({"error": "email parameter is required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'User does not exists'}), 404
    
    params = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": WS_FUNCTION,
        "moodlewsrestformat": "json",
        "criteria[0][key]": "email",
        "criteria[0][value]": email,
    }

    try:
        response = requests.get(MOODLE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("users"):
            user.confirmed = True
            user.role="kgu"
            db.session.commit()

        return jsonify(data), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 502    