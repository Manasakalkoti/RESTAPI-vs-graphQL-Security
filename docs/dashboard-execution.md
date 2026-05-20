# Dashboard Execution Guide

Step by step instructions to run the full demo with the web dashboard and terminal menu.

---

## Step 1 — Open VS Code Terminal

Press `` Ctrl + ` `` to open the terminal in VS Code.

---

## Step 2 — Activate the project

```bash
cd /Users/manasa/Desktop/RESTAPI-vs-graphQL-Security
source venv/bin/activate
```

You will see `(venv)` at the start of the line.

---

## Step 3 — Run the tests first (no servers needed)

```bash
pytest tests/ -v
```

Wait for `33 passed` to confirm everything works.

---

## Step 4 — Open 3 more terminals

In VS Code press `Ctrl + Shift + 5` to split terminals, or click the `+` button 3 times.

You should have **4 terminals total**.

---

## Step 5 — Terminal 1 — Start REST API (vulnerable)

```bash
cd /Users/manasa/Desktop/RESTAPI-vs-graphQL-Security
source venv/bin/activate
SECURE_MODE=false python src/rest_api/app.py
```

Wait until you see:
```
* Running on http://127.0.0.1:5050
```

> Leave this terminal running. Do not close it.

---

## Step 6 — Terminal 2 — Start GraphQL API (vulnerable)

```bash
cd /Users/manasa/Desktop/RESTAPI-vs-graphQL-Security
source venv/bin/activate
SECURE_MODE=false DISABLE_INTROSPECTION=false python src/graphql_api/app.py
```

Wait until you see:
```
* Running on http://127.0.0.1:5001
```

> Leave this terminal running. Do not close it.

---

## Step 7 — Terminal 3 — Start the Dashboard

```bash
cd /Users/manasa/Desktop/RESTAPI-vs-graphQL-Security
source venv/bin/activate
python src/dashboard/app.py
```

Wait until you see:
```
[Dashboard] Starting on http://127.0.0.1:5080
```

> Leave this terminal running. Do not close it.

---

## Step 8 — Open the Dashboard in browser

Open your browser and go to:

```
http://127.0.0.1:5080
```

You will see the dashboard with **green dots** showing both servers are up.

---

## Step 9 — Terminal 4 — Run attacks from terminal menu (optional)

```bash
cd /Users/manasa/Desktop/RESTAPI-vs-graphQL-Security
source venv/bin/activate
python src/dashboard/menu.py
```

- Press `1` through `6` to run each attack individually
- Press `A` to run all 6 attacks at once
- Press `Q` to quit

---

## Step 10 — Switch to SECURE mode to show defences

Stop Terminal 1 and Terminal 2 with `Ctrl+C`, then restart:

**Terminal 1:**
```bash
SECURE_MODE=true python src/rest_api/app.py
```

**Terminal 2:**
```bash
SECURE_MODE=true DISABLE_INTROSPECTION=true python src/graphql_api/app.py
```

Now run the same attacks from the dashboard or terminal menu — all 6 will show **BLOCKED**.

---

## Summary — What runs where

| Terminal | What runs | Port |
|----------|-----------|------|
| Terminal 1 | REST API server | 5050 |
| Terminal 2 | GraphQL API server | 5001 |
| Terminal 3 | Dashboard server | 5080 |
| Terminal 4 | Terminal menu (optional) | — |
| Browser | Dashboard UI | 5080 |

---

## What the dashboard shows

| Element | Description |
|---------|-------------|
| Green dot next to REST API | REST server is running on port 5050 |
| Green dot next to GraphQL | GraphQL server is running on port 5001 |
| VULNERABLE badge | Servers are in attack mode — attacks will SUCCEED |
| SECURED badge | Servers are in defence mode — attacks will be BLOCKED |
| Attack buttons 1–6 | Click to run each attack and see live output |
| SUCCEEDED badge (red) | Attack worked — vulnerability confirmed |
| BLOCKED badge (green) | Attack stopped — defence mechanism working |
| Summary row | Shows result of all 6 attacks at a glance |

---

## Attack reference

| # | Button | API | What it demonstrates |
|---|--------|-----|---------------------|
| 1 | BOLA / IDOR | REST | Alice reads Bob & Charlie's orders by changing the ID in the URL |
| 2 | Mass Assignment | REST | Injects `is_admin: true` inside a normal profile update |
| 3 | Excessive Data Exposure | REST | Reads `password_hash`, `reset_token`, `internal_notes` from response |
| 4 | Introspection Abuse | GraphQL | Sends `__schema` query to dump the full API structure |
| 5 | Depth / Circular DoS | GraphQL | Sends 8-level nested circular query to exhaust server CPU/RAM |
| 6 | Alias / Batching | GraphQL | Packs 50 login attempts into one HTTP request to bypass rate limiting |
