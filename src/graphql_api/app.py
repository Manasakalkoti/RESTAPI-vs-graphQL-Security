import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from strawberry.flask.views import GraphQLView
from dotenv import load_dotenv

from src.graphql_api.schema import schema
from src.graphql_api.security.introspection_protection import is_introspection_query
from src.graphql_api.security.depth_limit_protection import check_depth
from src.graphql_api.security.complexity_protection import check_complexity

load_dotenv()


def create_app(secure=None):
    app = Flask(__name__)
    CORS(app)

    if secure is None:
        secure = os.getenv("SECURE_MODE", "false").lower() == "true"

    disable_introspection = os.getenv("DISABLE_INTROSPECTION", "false").lower() == "true"
    app.config["SECURE_MODE"] = secure
    app.config["DISABLE_INTROSPECTION"] = disable_introspection

    # ── Security middleware — runs before every /graphql request ────────────
    @app.before_request
    def graphql_security_checks():
        if request.path != "/graphql" or request.method != "POST":
            return None

        if not app.config.get("SECURE_MODE", False):
            return None  # Vulnerable mode: skip all checks

        data = request.get_json(force=True, silent=True) or {}
        query = data.get("query", "")

        if not query:
            return None

        # 1. Introspection Protection
        if app.config.get("DISABLE_INTROSPECTION", False) and is_introspection_query(query):
            return jsonify({
                "errors": [{
                    "message": (
                        "Introspection is disabled on this server. "
                        "Schema exploration is not permitted in production."
                    )
                }]
            }), 400

        # 2. Depth Limit Protection
        try:
            depth = check_depth(query)
            g.query_depth = depth
        except ValueError as e:
            return jsonify({"errors": [{"message": str(e)}]}), 400

        # 3. Complexity / Alias-Batching Budget
        try:
            complexity = check_complexity(query)
            g.query_complexity = complexity
        except ValueError as e:
            return jsonify({"errors": [{"message": str(e)}]}), 400

        return None

    # ── GraphQL view ─────────────────────────────────────────────────────────
    app.add_url_rule(
        "/graphql",
        view_func=GraphQLView.as_view("graphql_view", schema=schema),
    )

    @app.route("/graphql/health", methods=["GET"])
    def gql_health():
        return jsonify({"status": "ok"}), 200

    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "name": "GraphQL API Security Lab",
            "mode": "SECURED" if secure else "VULNERABLE",
            "endpoint":  "POST /graphql",
            "playground": "GET  /graphql  (open in browser for GraphiQL)",
            "health":     "GET  /graphql/health",
        }), 200

    return app


if __name__ == "__main__":
    from src.common.seed import seed
    seed()

    mode = os.getenv("SECURE_MODE", "false")
    intro = os.getenv("DISABLE_INTROSPECTION", "false")
    port = int(os.getenv("GRAPHQL_API_PORT", 5001))
    print(f"\n[GraphQL API] Starting on port {port}  |  SECURE_MODE={mode}  |  DISABLE_INTROSPECTION={intro}\n")

    app = create_app()
    app.run(host="127.0.0.1", port=port, debug=True, use_reloader=False)
