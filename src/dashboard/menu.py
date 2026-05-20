"""
Terminal Menu UI
-----------------
Interactive menu to run any of the 6 attacks from the terminal.
Run with:  python src/dashboard/menu.py
"""
import os
import sys
import subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from colorama import Fore, Back, Style, init
init(autoreset=True)

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
ROOT = os.path.abspath(ROOT)

ATTACKS = [
    ("1", "BOLA / IDOR",              "REST",    "attacks/rest/bola_attack.py",
     "Alice reads Bob & Charlie's orders by changing the ID in the URL"),
    ("2", "Mass Assignment",           "REST",    "attacks/rest/mass_assignment_attack.py",
     "Injects is_admin:true into a normal profile update request"),
    ("3", "Excessive Data Exposure",   "REST",    "attacks/rest/excessive_data_attack.py",
     "Reads password_hash, reset_token, internal_notes from response"),
    ("4", "Introspection Abuse",       "GraphQL", "attacks/graphql/introspection_attack.py",
     "Sends __schema query to dump the full API structure"),
    ("5", "Depth / Circular DoS",      "GraphQL", "attacks/graphql/depth_dos_attack.py",
     "Sends 8-level nested circular query to exhaust server CPU/RAM"),
    ("6", "Alias / Batching",          "GraphQL", "attacks/graphql/alias_batching_attack.py",
     "Packs 50 login attempts into ONE HTTP request"),
]


def clear():
    os.system("clear")


def banner():
    print(Fore.CYAN + "╔" + "═" * 58 + "╗")
    print(Fore.CYAN + "║" + Fore.YELLOW + Style.BRIGHT +
          "   REST API vs GraphQL — Security Lab Demo".center(58) +
          Fore.CYAN + "║")
    print(Fore.CYAN + "╚" + "═" * 58 + "╝" + Style.RESET_ALL)
    print()


def menu():
    clear()
    banner()

    print(Fore.WHITE + Style.BRIGHT + "  Select an attack to run:\n")

    print(Fore.BLUE + "  ── REST API Attacks (port 5050) ──────────────────────")
    for key, name, api, _, desc in ATTACKS[:3]:
        print(f"  {Fore.YELLOW}[{key}]{Style.RESET_ALL}  {Fore.WHITE + Style.BRIGHT}{name}{Style.RESET_ALL}")
        print(f"       {Fore.WHITE + Style.DIM}{desc}{Style.RESET_ALL}")

    print()
    print(Fore.MAGENTA + "  ── GraphQL Attacks (port 5001) ────────────────────────")
    for key, name, api, _, desc in ATTACKS[3:]:
        print(f"  {Fore.YELLOW}[{key}]{Style.RESET_ALL}  {Fore.WHITE + Style.BRIGHT}{name}{Style.RESET_ALL}")
        print(f"       {Fore.WHITE + Style.DIM}{desc}{Style.RESET_ALL}")

    print()
    print(Fore.CYAN + "  ── Options ────────────────────────────────────────────")
    print(f"  {Fore.YELLOW}[A]{Style.RESET_ALL}  Run ALL 6 attacks")
    print(f"  {Fore.YELLOW}[Q]{Style.RESET_ALL}  Quit")
    print()


def run_script(script_path):
    print()
    result = subprocess.run(
        [sys.executable, os.path.join(ROOT, script_path)],
        cwd=ROOT,
    )
    print()
    input(Fore.CYAN + "  Press Enter to return to menu..." + Style.RESET_ALL)


def run_all():
    for _, name, _, script, _ in ATTACKS:
        print(Fore.CYAN + f"\n  Running: {name}" + Style.RESET_ALL)
        subprocess.run(
            [sys.executable, os.path.join(ROOT, script)],
            cwd=ROOT,
        )
    print()
    input(Fore.CYAN + "  All 6 attacks done. Press Enter to return to menu..." + Style.RESET_ALL)


def main():
    while True:
        menu()
        choice = input(f"  {Fore.GREEN}Enter choice: {Style.RESET_ALL}").strip().upper()

        if choice == "Q":
            clear()
            print(Fore.CYAN + "\n  Goodbye!\n" + Style.RESET_ALL)
            break
        elif choice == "A":
            clear()
            banner()
            run_all()
        elif choice in [a[0] for a in ATTACKS]:
            attack = next(a for a in ATTACKS if a[0] == choice)
            clear()
            banner()
            print(Fore.YELLOW + f"  Running Attack {choice}: {attack[1]}\n" + Style.RESET_ALL)
            run_script(attack[3])
        else:
            input(Fore.RED + "  Invalid choice. Press Enter to try again..." + Style.RESET_ALL)


if __name__ == "__main__":
    main()
