from flask import Blueprint, request, jsonify
from src.common.database import SessionLocal
from src.common.models import User
from src.common.auth import verify_password, generate_token

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json or {}
    username = data.get("username", "")
    password = data.get("password", "")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.password_hash):
            return jsonify({"error": "Invalid credentials"}), 401
        token = generate_token(user.id, user.username)
        return jsonify({"token": token, "user_id": user.id}), 200
    finally:
        db.close()
