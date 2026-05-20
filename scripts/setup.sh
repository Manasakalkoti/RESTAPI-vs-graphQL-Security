#!/usr/bin/env bash
# One-shot project setup: create venv, install deps, seed DB
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "[1/4] Creating virtual environment..."
python3 -m venv venv

echo "[2/4] Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo "[3/4] Copying .env config..."
[ -f .env ] || cp config/development.env .env

echo "[4/4] Seeding database..."
python -c "from src.common.seed import seed; seed()"

echo ""
echo "Setup complete."
echo "  Start REST API   : source venv/bin/activate && python src/rest_api/app.py"
echo "  Start GraphQL API: source venv/bin/activate && python src/graphql_api/app.py"
echo "  Run tests        : source venv/bin/activate && pytest tests/ -v"
echo "  Run all attacks  : bash scripts/run_attack_simulation.sh"
