from flask import Blueprint, request, jsonify, g, current_app
from src.common.database import SessionLocal
from src.common.models import User
from src.rest_api.middleware.auth import require_auth
from src.rest_api.security.mass_assignment_protection import (
    filter_allowed_fields, ALLOWED_USER_UPDATE_FIELDS,
)
from src.rest_api.security.data_exposure_protection import public_user_schema

users_bp = Blueprint("users", __name__)


# ── GET /api/users/profile ──────────────────────────────────────────────────

@users_bp.route("/api/users/profile", methods=["GET"])
@require_auth
def get_profile():
    secure = current_app.config.get("SECURE_MODE", False)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == g.current_user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        if secure:
            # SECURED: Marshmallow public schema strips sensitive fields
            return jsonify(public_user_schema.dump(user)), 200
        else:
            # VULNERABLE: Returns full database row including password_hash,
            # is_admin, reset_token, internal_notes
            return jsonify(user.to_dict()), 200
    finally:
        db.close()


# ── PUT /api/users/<id> ─────────────────────────────────────────────────────

@users_bp.route("/api/users/<int:user_id>", methods=["PUT"])
@require_auth
def update_user(user_id):
    secure = current_app.config.get("SECURE_MODE", False)
    data = request.json or {}
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        if secure:
            # SECURED: Only allowlisted fields are applied; is_admin, password_hash etc. ignored
            safe_data = filter_allowed_fields(data, ALLOWED_USER_UPDATE_FIELDS)
            for key, value in safe_data.items():
                setattr(user, key, value)
        else:
            # VULNERABLE: Every incoming field is written to the model — mass assignment
            for key, value in data.items():
                if hasattr(user, key):
                    setattr(user, key, value)

        db.commit()
        return jsonify({"message": "User updated"}), 200
    finally:
        db.close()


# ── GET /api/users/<id>  (admin helper — shows is_admin to confirm attack) ──

@users_bp.route("/api/users/<int:user_id>", methods=["GET"])
@require_auth
def get_user(user_id):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "Not found"}), 404
        return jsonify(user.to_dict()), 200
    finally:
        db.close()
