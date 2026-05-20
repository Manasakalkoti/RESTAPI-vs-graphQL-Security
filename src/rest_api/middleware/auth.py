from functools import wraps
from flask import request, g
from src.common.auth import decode_token
import jwt


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "").strip()
        if not token:
            return {"error": "Missing token"}, 401
        try:
            payload = decode_token(token)
            g.current_user_id = payload["user_id"]
            g.current_username = payload["username"]
        except jwt.ExpiredSignatureError:
            return {"error": "Token expired"}, 401
        except jwt.InvalidTokenError:
            return {"error": "Invalid token"}, 401
        return f(*args, **kwargs)
    return decorated
