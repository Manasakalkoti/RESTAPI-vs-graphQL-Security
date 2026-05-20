# Setup Guide

Step-by-step instructions for getting the project running locally from scratch.

---

## Prerequisites

| Requirement | Minimum Version | Check |
|-------------|----------------|-------|
| Python | 3.11+ | `python3 --version` |
| pip | 23+ | `pip --version` |
| git | any | `git --version` |

---

## Step 1 — Clone the Repository

```bash
git clone <repo-url>
cd RESTAPI-vs-graphQL-Security
```

---

## Step 2 — Create a Virtual Environment

Always use a virtual environment to keep dependencies isolated.

```bash
# Create the venv
python3 -m venv venv

# Activate it
# macOS / Linux
source venv/bin/activate

# Windows (Command Prompt)
venv\Scripts\activate.bat

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

You should see `(venv)` at the start of your terminal prompt.

---

## Step 3 — Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### What Gets Installed

| Package | Version | Purpose |
|---------|---------|---------|
| Flask | 3.0.3 | REST API framework |
| flask-cors | 4.0.1 | Cross-origin request headers |
| Flask-Limiter | 3.7.0 | Rate limiting middleware |
| strawberry-graphql[flask] | 0.235.1 | GraphQL framework |
| graphql-core | 3.2.3 | GraphQL AST parsing and validation |
| SQLAlchemy | 2.0.30 | ORM and database abstraction |
| Flask-SQLAlchemy | 3.1.1 | Flask + SQLAlchemy integration |
| PyJWT | 2.8.0 | JWT token generation and verification |
| bcrypt | 4.1.3 | Password hashing |
| cryptography | 42.0.8 | Cryptographic primitives (JWT dependency) |
| marshmallow | 3.21.3 | Input validation and response serialisation |
| marshmallow-sqlalchemy | 1.0.0 | Marshmallow + SQLAlchemy integration |
| graphql-query-complexity | 0.1.0 | GraphQL query complexity calculation |
| python-dotenv | 1.0.1 | Load `.env` files into environment |
| requests | 2.32.3 | HTTP client used in attack scripts |
| pytest | 8.2.2 | Test runner |
| pytest-flask | 1.3.0 | Flask test client integration |
| pytest-cov | 5.0.0 | Code coverage reporting |
| colorama | 0.4.6 | Coloured terminal output in attack scripts |
| tabulate | 0.9.0 | Table formatting in attack output |

Verify the install completed without errors:

```bash
pip list
```

---

## Step 4 — Configure Environment Variables

Copy the development environment file and edit it:

```bash
cp config/development.env .env
```

Open `.env` and set the values:

```env
# .env

# Flask
FLASK_ENV=development
FLASK_DEBUG=true

# Server ports
REST_API_PORT=5000
GRAPHQL_API_PORT=5001

# Database
DATABASE_URL=sqlite:///lab.db

# JWT — change this to any long random string
JWT_SECRET=change-this-to-a-long-random-secret-key

# Security toggle
# Set to "false" for attack simulation, "true" for secured mode
SECURE_MODE=false

# GraphQL introspection
# Set to "false" in development, "true" in production
DISABLE_INTROSPECTION=false
```

> **Never commit `.env` to git.** It is already listed in `.gitignore`.

Generate a strong `JWT_SECRET`:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## Step 5 — Initialise the Database

Create the SQLite database and populate it with seed data:

```bash
python3 scripts/setup.sh
# or directly:
python3 -c "from src.common.database import init_db; init_db()"
```

This creates `lab.db` in the project root with:
- 3 test users (alice, bob, charlie)
- 10 posts per user
- 5 orders per user

---

## Step 6 — Start the APIs

Open two terminal windows, both with the venv activated.

**Terminal 1 — REST API (port 5000)**

```bash
python src/rest_api/app.py
```

Expected output:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

**Terminal 2 — GraphQL API (port 5001)**

```bash
python src/graphql_api/app.py
```

Expected output:
```
 * Running on http://127.0.0.1:5001
 * GraphQL endpoint: http://127.0.0.1:5001/graphql
```

---

## Step 7 — Verify the Setup

**Check REST API is up:**

```bash
curl http://localhost:5050/api/health
# Expected: {"status": "ok"}
```

**Check GraphQL API is up:**

```bash
curl -X POST http://localhost:5001/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}'
# Expected: {"data": {"__typename": "Query"}}
```

**Run the test suite:**

```bash
pytest tests/ -v
```

All tests should pass (or be skipped if the server is not running).

---

## Switching Between Vulnerable and Secured Mode

### Vulnerable Mode (for attack simulation)

```bash
SECURE_MODE=false python src/rest_api/app.py
SECURE_MODE=false DISABLE_INTROSPECTION=false python src/graphql_api/app.py
```

### Secured Mode (for defence verification)

```bash
SECURE_MODE=true python src/rest_api/app.py
SECURE_MODE=true DISABLE_INTROSPECTION=true python src/graphql_api/app.py
```

Or update `.env` and restart both servers.

---

## Common Errors and Fixes

### `ModuleNotFoundError: No module named 'flask'`

The venv is not activated. Run:
```bash
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```

### `Address already in use` on port 5000 or 5001

Another process is using the port. Find and kill it:
```bash
# macOS / Linux
lsof -i :5000
kill -9 <PID>

# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### `sqlalchemy.exc.OperationalError: unable to open database file`

The `lab.db` file does not exist yet. Run Step 5 again:
```bash
python3 -c "from src.common.database import init_db; init_db()"
```

### `jwt.exceptions.InvalidSignatureError`

The `JWT_SECRET` in `.env` does not match the one used to generate existing tokens. Clear
your tokens and re-login, or re-generate a fresh secret and restart both servers.

### `pip install` fails with SSL errors

Upgrade pip and try again:
```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

---

## Deactivating the Virtual Environment

When you are done working:

```bash
deactivate
```

---

## Full Reset

To wipe all state and start fresh:

```bash
deactivate
rm -rf venv lab.db
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 -c "from src.common.database import init_db; init_db()"
```
