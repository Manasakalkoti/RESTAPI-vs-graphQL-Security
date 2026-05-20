"""
Excessive Data Exposure Attack — "The TMI Response"
=====================================================
Logs in as alice and calls GET /api/users/profile.
Checks the raw JSON response for sensitive fields that should never be sent
(password_hash, is_admin, reset_token, internal_notes).

Run against VULNERABLE server:  SECURE_MODE=false  → sensitive fields visible
Run against SECURED   server:   SECURE_MODE=true   → only safe public fields
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import requests
from colorama import Fore, Style, init

init(autoreset=True)

BASE = "http://localhost:5050"
ALICE_CREDS = {"username": "alice", "password": "password123"}

SENSITIVE_FIELDS = ["password_hash", "is_admin", "reset_token", "internal_notes"]
SAFE_FIELDS      = ["id", "username", "email", "bio"]


def login(creds: dict) -> str:
    r = requests.post(f"{BASE}/api/auth/login", json=creds, timeout=5)
    r.raise_for_status()
    return r.json()["token"]


def run_attack(label: str, token: str):
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"  EXCESSIVE DATA EXPOSURE  [{label}]")
    print(f"{'='*60}{Style.RESET_ALL}")
    print(f"Logged in as: {ALICE_CREDS['username']}")
    print(f"Calling GET /api/users/profile ...\n")

    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE}/api/users/profile", headers=headers, timeout=5)
    data = r.json()

    print("Response fields received:")
    exposed = []
    for field, value in data.items():
        if field in SENSITIVE_FIELDS:
            exposed.append(field)
            print(f"  {Fore.RED}[SENSITIVE]{Style.RESET_ALL} {field}: {str(value)[:60]}")
        else:
            print(f"  {Fore.GREEN}[safe]     {Style.RESET_ALL} {field}: {value}")

    print()
    if exposed:
        print(f"{Fore.RED}[RESULT] ATTACK SUCCEEDED — "
              f"{len(exposed)} sensitive field(s) exposed in response: {exposed}{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}[RESULT] ATTACK BLOCKED — "
              f"0 sensitive fields in response. Public schema filter works!{Style.RESET_ALL}")


if __name__ == "__main__":
    token = login(ALICE_CREDS)
    run_attack("live server", token)
