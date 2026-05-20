#!/usr/bin/env bash
# ============================================================
#  Full Attack + Defense Simulation
#  Starts both servers, runs all 6 attacks in VULNERABLE mode,
#  then restarts in SECURE mode and runs all 6 again.
# ============================================================

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/venv/bin/activate"

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'
YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'

source "$VENV"
cd "$ROOT"

# Seed the database once
python -c "from src.common.seed import seed; seed()" 2>/dev/null

kill_servers() {
  pkill -f "src/rest_api/app.py"    2>/dev/null || true
  pkill -f "src/graphql_api/app.py" 2>/dev/null || true
  sleep 1
}

start_servers() {
  local mode=$1
  export SECURE_MODE=$mode
  export DISABLE_INTROSPECTION=$([[ "$mode" == "true" ]] && echo "true" || echo "false")

  python src/rest_api/app.py    > /tmp/rest_api.log    2>&1 &
  python src/graphql_api/app.py > /tmp/graphql_api.log 2>&1 &

  echo -e "${CYAN}Waiting for servers to start...${NC}"
  sleep 3

  # Verify both are up
  curl -sf http://localhost:5050/api/health    > /dev/null || { echo "REST API failed to start";    exit 1; }
  curl -sf http://localhost:5001/graphql/health > /dev/null || { echo "GraphQL API failed to start"; exit 1; }
  echo -e "${GREEN}Both servers running.${NC}"
}

run_all_attacks() {
  python attacks/rest/bola_attack.py
  python attacks/rest/mass_assignment_attack.py
  python attacks/rest/excessive_data_attack.py
  python attacks/graphql/introspection_attack.py
  python attacks/graphql/depth_dos_attack.py
  python attacks/graphql/alias_batching_attack.py
}

# ── PHASE 1: VULNERABLE MODE ─────────────────────────────────────────────────
echo -e "\n${BOLD}${RED}╔══════════════════════════════════════════════════╗"
echo -e "║  PHASE 1 — VULNERABLE MODE  (SECURE_MODE=false) ║"
echo -e "╚══════════════════════════════════════════════════╝${NC}\n"

kill_servers
start_servers "false"
run_all_attacks
kill_servers

# ── PHASE 2: SECURED MODE ─────────────────────────────────────────────────────
echo -e "\n${BOLD}${GREEN}╔══════════════════════════════════════════════════╗"
echo -e "║  PHASE 2 — SECURED MODE     (SECURE_MODE=true)  ║"
echo -e "╚══════════════════════════════════════════════════╝${NC}\n"

start_servers "true"
run_all_attacks
kill_servers

echo -e "\n${BOLD}${CYAN}Simulation complete. All 6 attacks demonstrated in both modes.${NC}\n"
