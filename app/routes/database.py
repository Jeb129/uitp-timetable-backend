from flask import Blueprint, request, jsonify
from http import HTTPStatus
import requests
from models import *
from auth import jwt_required

db_bp = Blueprint('db', __name__, url_prefix='/database')

@db_bp.route("/get/<model_name>", methods=["POST"])
def get(model_name):
    model_name = model_name.lower()

    if model_name not in WEB_ABLE_MODELS:
        return jsonify({"error": "model not found"}), HTTPStatus.INTERNAL_SERVER_ERROR
    try:
        model = WEB_ABLE_MODELS[model_name]
        filters = request.get_json()
        if not filters:
            return jsonify([m.to_dict() for m in model.query.all()])
        
        query = model.query

        for key, value in filters.items():
            if not hasattr(model, key):
                return jsonify({"error": f"Invalid field: {key}"}), HTTPStatus.BAD_REQUEST

            query = query.filter(getattr(model, key) == value)

        results = query.all()
        return jsonify([r.to_dict() for r in results])
    except Exception as e:
        return jsonify({'error': f'Failed to get object: {str(e)}'}), HTTPStatus.INTERNAL_SERVER_ERROR  

    

@db_bp.route("/update/<model_name>", methods=["POST"])
@jwt_required
def udate(model_name):
    model_name = model_name.lower()

    if model_name not in WEB_ABLE_MODELS:
        return jsonify({"error": "model not found"}), HTTPStatus.INTERNAL_SERVER_ERROR
    
    model = WEB_ABLE_MODELS[model_name]
    try:
        filters = request.get_json()
        if not filters:
            return jsonify({"error": "Update body wasn't specified"}), HTTPStatus.BAD_REQUEST
        
        item = model.query.filter(getattr(model, "id") == filters["id"])
        if not item:
            return jsonify({"error": f"{model_name} with id {filters["id"]} not found"}), HTTPStatus.NOT_FOUND
        
        for key, value in filters.items():
            if not hasattr(model, key):
                return jsonify({"error": f"Invalid field: {key}"}), HTTPStatus.NOT_FOUND
            setattr(item,key,value)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update object: {str(e)}'}), HTTPStatus.INTERNAL_SERVER_ERROR  


