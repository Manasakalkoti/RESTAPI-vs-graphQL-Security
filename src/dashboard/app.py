import os
import sys
import subprocess
import requests as http
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

REST_BASE    = "http://127.0.0.1:5050"
GRAPHQL_BASE = "http://127.0.0.1:5001"


def server_status(url):
    try:
        http.get(url, timeout=2)
        return True
    except Exception:
        return False


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def status():
    return jsonify({
        "rest":    server_status(f"{REST_BASE}/api/health"),
        "graphql": server_status(f"{GRAPHQL_BASE}/graphql/health"),
    })


@app.route("/api/run/<attack>", methods=["POST"])
def run_attack(attack):
    mode = request.json.get("mode", "vulnerable")

    ATTACKS = {
        "bola":          ("rest",    "attacks/rest/bola_attack.py"),
        "mass":          ("rest",    "attacks/rest/mass_assignment_attack.py"),
        "exposure":      ("rest",    "attacks/rest/excessive_data_attack.py"),
        "introspection": ("graphql", "attacks/graphql/introspection_attack.py"),
        "depth":         ("graphql", "attacks/graphql/depth_dos_attack.py"),
        "batching":      ("graphql", "attacks/graphql/alias_batching_attack.py"),
    }

    if attack not in ATTACKS:
        return jsonify({"error": "Unknown attack"}), 400

    project_root = os.path.join(os.path.dirname(__file__), "..", "..")
    script_path  = os.path.join(project_root, ATTACKS[attack][1])
    python_bin   = sys.executable

    try:
        result = subprocess.run(
            [python_bin, script_path],
            capture_output=True, text=True, timeout=30,
            cwd=os.path.abspath(project_root),
        )
        raw = result.stdout + result.stderr
        # strip urllib warning lines
        lines = [l for l in raw.splitlines()
                 if "NotOpenSSLWarning" not in l and "warnings.warn" not in l]
        return jsonify({"output": "\n".join(lines)})
    except subprocess.TimeoutExpired:
        return jsonify({"output": "Attack timed out after 30s."}), 200
    except Exception as e:
        return jsonify({"output": f"Error: {e}"}), 500


if __name__ == "__main__":
    port = int(os.getenv("DASHBOARD_PORT", 5080))
    print(f"\n[Dashboard] Starting on http://127.0.0.1:{port}\n")
    app.run(host="127.0.0.1", port=port, debug=False)
