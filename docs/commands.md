# Commands Reference

All commands needed to run, test, and demonstrate the project.

---

## Step 0 — Always activate venv first

```bash
cd /Users/manasa/Desktop/RESTAPI-vs-graphQL-Security
source venv/bin/activate
```

---

## Step 1 — Run Tests (no servers needed)

```bash
pytest tests/ -v
```

---

## Step 2 — Demonstrate Attacks (servers required)

### Terminal 1 — Start REST API (vulnerable)

```bash
cd /Users/manasa/Desktop/RESTAPI-vs-graphQL-Security
source venv/bin/activate
SECURE_MODE=false python src/rest_api/app.py
```

### Terminal 2 — Start GraphQL API (vulnerable)

```bash
cd /Users/manasa/Desktop/RESTAPI-vs-graphQL-Security
source venv/bin/activate
SECURE_MODE=false DISABLE_INTROSPECTION=false python src/graphql_api/app.py
```

### Terminal 3 — Run all 6 attacks (vulnerable mode — all should SUCCEED)

```bash
cd /Users/manasa/Desktop/RESTAPI-vs-graphQL-Security
source venv/bin/activate

# Attack 1 — BOLA / IDOR
python attacks/rest/bola_attack.py

# Attack 2 — Mass Assignment
python attacks/rest/mass_assignment_attack.py

# Attack 3 — Excessive Data Exposure
python attacks/rest/excessive_data_attack.py

# Attack 4 — Introspection Abuse
python attacks/graphql/introspection_attack.py

# Attack 5 — Depth / Circular DoS
python attacks/graphql/depth_dos_attack.py

# Attack 6 — Alias / Batching
python attacks/graphql/alias_batching_attack.py
```

---

## Step 3 — Demonstrate Security Mechanisms

Stop servers in Terminal 1 and 2 with `Ctrl+C`, then:

### Terminal 1 — Restart REST API (secured)

```bash
cd /Users/manasa/Desktop/RESTAPI-vs-graphQL-Security
source venv/bin/activate
SECURE_MODE=true python src/rest_api/app.py
```

### Terminal 2 — Restart GraphQL API (secured)

```bash
cd /Users/manasa/Desktop/RESTAPI-vs-graphQL-Security
source venv/bin/activate
SECURE_MODE=true DISABLE_INTROSPECTION=true python src/graphql_api/app.py
```

### Terminal 3 — Run same 6 attacks (secured mode — all should be BLOCKED)

```bash
# Attack 1 — BOLA / IDOR
python attacks/rest/bola_attack.py

# Attack 2 — Mass Assignment
python attacks/rest/mass_assignment_attack.py

# Attack 3 — Excessive Data Exposure
python attacks/rest/excessive_data_attack.py

# Attack 4 — Introspection Abuse
python attacks/graphql/introspection_attack.py

# Attack 5 — Depth / Circular DoS
python attacks/graphql/depth_dos_attack.py

# Attack 6 — Alias / Batching
python attacks/graphql/alias_batching_attack.py
```

---

## All-in-One — Single command does everything automatically

```bash
cd /Users/manasa/Desktop/RESTAPI-vs-graphQL-Security
source venv/bin/activate
bash scripts/run_attack_simulation.sh
```

---

## Attack Reference

| # | File | API | Attack Name | What It Does |
|---|------|-----|------------|-------------|
| 1 | `attacks/rest/bola_attack.py` | REST | BOLA / IDOR | Alice reads Bob & Charlie's orders by changing the ID in the URL |
| 2 | `attacks/rest/mass_assignment_attack.py` | REST | Mass Assignment | Injects `is_admin: true` inside a normal profile update |
| 3 | `attacks/rest/excessive_data_attack.py` | REST | Excessive Data Exposure | Reads `password_hash`, `reset_token`, `internal_notes` from the response |
| 4 | `attacks/graphql/introspection_attack.py` | GraphQL | Introspection Abuse | Sends `__schema` query to dump the full API structure |
| 5 | `attacks/graphql/depth_dos_attack.py` | GraphQL | Depth / Circular DoS | Sends 8-level nested circular query to exhaust server CPU/RAM |
| 6 | `attacks/graphql/alias_batching_attack.py` | GraphQL | Alias / Batching | Packs 50 login attempts into one HTTP request to bypass rate limiting |

---

## Browser URLs (while servers are running)

| URL | What you see |
|-----|-------------|
| `http://127.0.0.1:5050/` | REST API info + all endpoint paths |
| `http://127.0.0.1:5050/api/health` | REST health check |
| `http://127.0.0.1:5001/` | GraphQL API info |
| `http://127.0.0.1:5001/graphql` | GraphiQL interactive playground |

---

## Useful extras

```bash
# Run tests with coverage report
pytest tests/ -v --cov=src --cov-report=term-missing

# Run a single test file
pytest tests/test_rest_vulnerabilities.py -v
pytest tests/test_rest_security.py -v
pytest tests/test_graphql_vulnerabilities.py -v
pytest tests/test_graphql_security.py -v

# Seed the database manually
python -c "from src.common.seed import seed; seed()"

# Reset the database completely
rm lab.db && python -c "from src.common.seed import seed; seed()"
```
