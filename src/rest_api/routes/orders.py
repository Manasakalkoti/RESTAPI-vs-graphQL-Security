from flask import Blueprint, jsonify, g, current_app
from src.common.database import SessionLocal
from src.common.models import Order
from src.rest_api.middleware.auth import require_auth
from src.rest_api.security.bola_protection import get_order_with_ownership_check
from src.rest_api.security.data_exposure_protection import (
    public_order_schema, public_orders_schema,
)

orders_bp = Blueprint("orders", __name__)


# ── GET /api/orders/<id> ────────────────────────────────────────────────────

@orders_bp.route("/api/orders/<int:order_id>", methods=["GET"])
@require_auth
def get_order(order_id):
    secure = current_app.config.get("SECURE_MODE", False)
    db = SessionLocal()
    try:
        if secure:
            # SECURED: Ownership check — order.user_id must match logged-in user
            order = get_order_with_ownership_check(order_id, g.current_user_id)
            if not order:
                # Same 404 for not-found and not-owned — no information leak
                return jsonify({"error": "Not found"}), 404
            return jsonify(public_order_schema.dump(order)), 200
        else:
            # VULNERABLE: Fetches by ID only — BOLA/IDOR — any authenticated user
            # can read any other user's orders by changing the ID
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                return jsonify({"error": "Not found"}), 404
            return jsonify(order.to_dict()), 200
    finally:
        db.close()


# ── GET /api/orders  (list caller's own orders) ─────────────────────────────

@orders_bp.route("/api/orders", methods=["GET"])
@require_auth
def list_orders():
    db = SessionLocal()
    try:
        orders = db.query(Order).filter(Order.user_id == g.current_user_id).all()
        return jsonify(public_orders_schema.dump(orders)), 200
    finally:
        db.close()
