from flask import Blueprint, request, jsonify
import requests

MOODLE_URL = "http://localhost:5002/webservice/rest/server.php" # Тут апи сдо должно быть но пока что локальное (кто хочет - ставьте сервер мудла себе сами.)
MOODLE_TOKEN = "YOUR_MOODLE_TOKEN" # Аналогично предыдущему пункту нужен  токен от сдо с правами moodle/user:viewdetails.
WS_FUNCTION = "core_user_get_users" # имя метода

moodle_bp = Blueprint('moodle', __name__, url_prefix='/moodle')

@moodle_bp.route("/user",methods=['GET'])
def get_moodle_user():
    email = request.args.get("email")

    if not email:
        return jsonify({"error": "email parameter is required"}), 400

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
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 502

    return jsonify(data)