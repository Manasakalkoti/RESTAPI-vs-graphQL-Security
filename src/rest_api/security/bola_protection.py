"""
BOLA / IDOR Protection
-----------------------
Instead of fetching a resource by ID alone, the query adds an ownership
condition: resource.user_id must equal the currently authenticated user's ID.

From the PDF:
  "The server checks two things together:
   - Whether the requested resource exists
   - Whether the currently logged-in user actually owns that resource"
"""
from src.common.database import SessionLocal
from src.common.models import Order


def get_order_with_ownership_check(order_id: int, current_user_id: int):
    """
    Returns the order only if it exists AND belongs to current_user_id.
    Returns None otherwise — caller should respond with 404 to avoid
    leaking whether the resource exists at all.
    """
    db = SessionLocal()
    try:
        order = (
            db.query(Order)
            .filter(Order.id == order_id, Order.user_id == current_user_id)
            .first()
        )
        return order
    finally:
        db.close()
