import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()


def create_app(secure=None):
    app = Flask(__name__)
    CORS(app)

    if secure is None:
        secure = os.getenv("SECURE_MODE", "false").lower() == "true"

    app.config["SECURE_MODE"] = secure
    app.config["SECRET_KEY"] = os.getenv("JWT_SECRET", "dev-secret")

    from src.rest_api.routes.auth import auth_bp
    from src.rest_api.routes.users import users_bp
    from src.rest_api.routes.orders import orders_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(orders_bp)

    @app.route("/", methods=["GET"])
    def index():
        from flask import jsonify
        return jsonify({
            "name": "REST API Security Lab",
            "mode": "SECURED" if secure else "VULNERABLE",
            "endpoints": {
                "health":  "GET  /api/health",
                "login":   "POST /api/auth/login",
                "profile": "GET  /api/users/profile",
                "update":  "PUT  /api/users/<id>",
                "order":   "GET  /api/orders/<id>",
                "orders":  "GET  /api/orders",
            }
        }), 200

    return app


if __name__ == "__main__":
    from src.common.seed import seed
    seed()

    mode = os.getenv("SECURE_MODE", "false")
    port = int(os.getenv("REST_API_PORT", 5000))
    print(f"\n[REST API] Starting on port {port}  |  SECURE_MODE={mode}\n")

    app = create_app()
    app.run(host="127.0.0.1", port=port, debug=True, use_reloader=False)
