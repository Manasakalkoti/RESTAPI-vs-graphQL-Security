# Tech Stack

Complete reference of every technology, library, tool, and package used in this project —
what it is, why it was chosen, and exactly where it is used.

---

## Language

### Python 3.9.6
- **What it is:** The programming language the entire project is written in.
- **Why used:** Mature security ecosystem, readable syntax, excellent library support for both web frameworks and attack scripting.
- **Used in:** Every file in `src/`, `attacks/`, `tests/`, `scripts/`.

---

## Web Frameworks

### Flask 3.0.3
- **What it is:** A lightweight Python web framework for building HTTP APIs.
- **Why used:** Minimal and explicit — vulnerabilities and defences are clearly visible in the code without framework magic hiding them.
- **Used in:**
  - `src/rest_api/app.py` — REST API server
  - `src/graphql_api/app.py` — GraphQL API server
  - `src/dashboard/app.py` — Web dashboard server
- **Key features used:** Blueprints, `before_request` hooks, `jsonify`, `g` context, `current_app`

### flask-cors 4.0.1
- **What it is:** Flask extension that adds Cross-Origin Resource Sharing (CORS) headers.
- **Why used:** Allows the browser dashboard to call the REST and GraphQL APIs from a different port without being blocked.
- **Used in:** `src/rest_api/app.py`, `src/graphql_api/app.py`

### Flask-Limiter 3.7.0
- **What it is:** Flask extension for rate limiting incoming requests.
- **Why used:** Installed to demonstrate that standard rate limiting alone cannot stop GraphQL alias/batching attacks — one HTTP request containing 50 operations bypasses request-count limits entirely.
- **Used in:** `src/graphql_api/app.py`

---

## GraphQL

### strawberry-graphql 0.235.1
- **What it is:** A modern Python GraphQL framework that uses Python type hints to define schemas.
- **Why used:** Type-safe, clean API, good Flask integration, supports custom middleware and extensions.
- **Used in:**
  - `src/graphql_api/schema.py` — defines all GraphQL types, queries, mutations
  - `src/graphql_api/app.py` — mounts GraphQL endpoint via `GraphQLView`
- **Key features used:**
  - `@strawberry.type` — defines `UserType`, `PostType`, `OrderType`, `AuthResponse`
  - `@strawberry.field` — defines field resolvers including circular relationships
  - `@strawberry.mutation` — defines `login` and `register` mutations
  - `strawberry.Schema` — assembles the final schema
  - `GraphQLView` — Flask view that handles GraphQL POST requests

### graphql-core 3.2.3
- **What it is:** The core Python implementation of the GraphQL specification.
- **Why used:** Used directly to parse query strings into AST (Abstract Syntax Tree) for depth and complexity analysis — before queries reach the strawberry resolver.
- **Used in:**
  - `src/graphql_api/security/depth_limit_protection.py` — `parse()` to build AST, walk `FieldNode` tree to count depth
  - `src/graphql_api/security/complexity_protection.py` — `parse()` to build AST, sum field costs
- **Key classes used:** `parse()`, `FieldNode`, `InlineFragmentNode`

---

## Database and ORM

### SQLAlchemy 2.0.30
- **What it is:** Python SQL toolkit and Object Relational Mapper (ORM).
- **Why used:** Explicit query building makes ownership checks (BOLA defence) and model definitions clearly visible. Parameterised queries prevent SQL injection by default.
- **Used in:**
  - `src/common/database.py` — engine, session factory, `Base` class, `init_db()`
  - `src/common/models.py` — `User`, `Post`, `Order` model definitions
  - All route files — `SessionLocal()` for database access
- **Key features used:**
  - `DeclarativeBase` — base class for all models
  - `SessionLocal` — database session factory
  - `relationship()` — circular `User ↔ Post` relationship (depth DoS enabler)
  - `Column`, `ForeignKey` — model field definitions

### Flask-SQLAlchemy 3.1.1
- **What it is:** Flask extension that integrates SQLAlchemy with the Flask application lifecycle.
- **Why used:** Provides clean app context management for database sessions.
- **Used in:** `src/rest_api/app.py`, `src/graphql_api/app.py`

### SQLite 3.39.5 (built into Python)
- **What it is:** A file-based relational database — no separate server process required.
- **Why used:** Zero setup — the database is a single file (`lab.db`). Perfect for a self-contained security lab.
- **Database file:** `lab.db` (production/demo), `test_lab.db` (tests)
- **Used in:** All database operations via SQLAlchemy

---

## Authentication and Security

### PyJWT 2.8.0
- **What it is:** Python library for creating and verifying JSON Web Tokens (JWT).
- **Why used:** Industry-standard token-based authentication. The JWT holds the `user_id` which is used in the BOLA ownership check.
- **Used in:**
  - `src/common/auth.py` — `generate_token()`, `decode_token()`
  - `src/rest_api/middleware/auth.py` — `require_auth` decorator decodes token on every request
- **Algorithm used:** `HS256`

### bcrypt 4.1.3
- **What it is:** Password hashing library using the bcrypt algorithm.
- **Why used:** Secure one-way password hashing. Even though `password_hash` is exposed in the vulnerable mode, bcrypt ensures raw passwords are never stored in plain text.
- **Used in:**
  - `src/common/auth.py` — `hash_password()`, `verify_password()`
  - `src/common/seed.py` — hashes all seed user passwords

### cryptography 42.0.8
- **What it is:** Low-level cryptographic primitives library.
- **Why used:** Required as a dependency by PyJWT for certain signing algorithms.
- **Used in:** Indirect dependency of PyJWT.

---

## Input Validation and Serialisation

### marshmallow 3.21.3
- **What it is:** Python object serialisation and deserialisation library with schema validation.
- **Why used:** Defines strict public schemas for API responses — the core mechanism behind the Excessive Data Exposure defence. Only fields explicitly listed in the schema are included in the response.
- **Used in:**
  - `src/rest_api/security/data_exposure_protection.py`
    - `PublicUserSchema` — exposes only `id`, `username`, `email`, `bio`
    - `PublicOrderSchema` — exposes only `id`, `item_name`, `amount`
- **Key features used:** `Schema`, `fields.Int()`, `fields.Str()`, `fields.Float()`, `.dump()`

### marshmallow-sqlalchemy 1.0.0
- **What it is:** Integration layer between Marshmallow and SQLAlchemy models.
- **Why used:** Allows Marshmallow schemas to work directly with SQLAlchemy model instances without manual conversion.
- **Used in:** `src/rest_api/security/data_exposure_protection.py`

---

## Environment Configuration

### python-dotenv 1.0.1
- **What it is:** Loads environment variables from a `.env` file into `os.environ`.
- **Why used:** Keeps secrets (JWT secret key) and configuration (ports, modes) out of source code.
- **Used in:** All `app.py` files via `load_dotenv()`
- **Config files:**
  - `.env` — active config (gitignored)
  - `config/development.env` — development defaults
  - `config/production.env` — production defaults

---

## HTTP Client (Attack Scripts)

### requests 2.32.3
- **What it is:** Python HTTP client library.
- **Why used:** Used exclusively in attack scripts to send HTTP requests to the vulnerable servers — login, GET orders, PUT users, POST GraphQL queries.
- **Used in:**
  - `attacks/rest/bola_attack.py`
  - `attacks/rest/mass_assignment_attack.py`
  - `attacks/rest/excessive_data_attack.py`
  - `attacks/graphql/introspection_attack.py`
  - `attacks/graphql/depth_dos_attack.py`
  - `attacks/graphql/alias_batching_attack.py`
  - `src/dashboard/app.py` — status health checks

---

## Testing

### pytest 8.2.2
- **What it is:** Python testing framework.
- **Why used:** Clean fixture system, readable assertions, excellent plugin ecosystem.
- **Used in:** All files in `tests/`
- **Test files:**
  - `tests/test_rest_vulnerabilities.py` — proves REST attacks succeed on vulnerable API
  - `tests/test_rest_security.py` — proves REST attacks are blocked on secured API
  - `tests/test_graphql_vulnerabilities.py` — proves GraphQL attacks succeed on vulnerable API
  - `tests/test_graphql_security.py` — proves GraphQL attacks are blocked on secured API

### pytest-flask 1.3.0
- **What it is:** pytest plugin for testing Flask applications.
- **Why used:** Provides Flask test client integration — tests run without needing a live server.
- **Used in:** `tests/conftest.py` — `app.test_client()` fixture

### pytest-cov 5.0.0
- **What it is:** pytest plugin for measuring code coverage.
- **Why used:** Reports which lines of source code are exercised by tests.
- **Command:** `pytest tests/ -v --cov=src --cov-report=term-missing`

### httpretty 1.1.4
- **What it is:** HTTP request mocking library for tests.
- **Why used:** Available for mocking external HTTP calls in tests if needed.
- **Used in:** Available as dependency, used if external HTTP mocking is needed.

---

## Terminal UI

### colorama 0.4.6
- **What it is:** Cross-platform library for coloured terminal text on Windows, macOS, and Linux.
- **Why used:** Makes attack script output readable at a glance — red for attack succeeded, green for blocked, yellow for headers.
- **Used in:** All 6 attack scripts, `src/dashboard/menu.py`
- **Colours used:**
  - `Fore.RED` — attack succeeded, sensitive fields, unauthorised access
  - `Fore.GREEN` — attack blocked, safe fields, owned records
  - `Fore.YELLOW` — section headers, injected field labels
  - `Fore.CYAN` — banner borders, info messages

### click 8.1.7
- **What it is:** Python package for building command-line interfaces.
- **Why used:** Available for building CLI utilities and helper scripts.
- **Used in:** Available as dependency for CLI tooling.

### tabulate 0.9.0
- **What it is:** Python library for formatting data as text tables.
- **Why used:** Available for printing tabular output in attack scripts or reports.
- **Used in:** Available as dependency for table formatting.

---

## Dashboard (Web UI)

### HTML5 + CSS3 + Vanilla JavaScript
- **What it is:** Standard web technologies — no frontend framework used.
- **Why used:** Zero additional dependencies. The dashboard runs entirely from the Flask template without needing React, Vue, or any npm packages.
- **Used in:** `src/dashboard/templates/index.html`
- **Key features used:**
  - CSS Grid — two-column attack panel layout
  - CSS custom properties — dark theme colour system
  - `fetch()` API — calls `/api/run/<attack>` and `/api/status` endpoints
  - `setInterval()` — polls server status every 3 seconds
  - `innerHTML` colorization — colours output lines by keyword matching

---

## Package Summary Table

| Package | Version | Category | Purpose |
|---------|---------|----------|---------|
| Python | 3.9.6 | Language | Core language |
| Flask | 3.0.3 | Framework | REST API + Dashboard server |
| flask-cors | 4.0.1 | Framework | Cross-origin request headers |
| Flask-Limiter | 3.7.0 | Framework | Rate limiting middleware |
| strawberry-graphql | 0.235.1 | GraphQL | GraphQL schema + server |
| graphql-core | 3.2.3 | GraphQL | AST parsing for depth/complexity checks |
| SQLAlchemy | 2.0.30 | Database | ORM and query builder |
| Flask-SQLAlchemy | 3.1.1 | Database | Flask + SQLAlchemy integration |
| SQLite | 3.39.5 | Database | File-based database (no server needed) |
| PyJWT | 2.8.0 | Auth | JWT token generation and verification |
| bcrypt | 4.1.3 | Auth | Password hashing |
| cryptography | 42.0.8 | Auth | Cryptographic primitives (JWT dependency) |
| marshmallow | 3.21.3 | Validation | Public response schema (data exposure defence) |
| marshmallow-sqlalchemy | 1.0.0 | Validation | Marshmallow + SQLAlchemy integration |
| python-dotenv | 1.0.1 | Config | Load `.env` environment variables |
| requests | 2.32.3 | HTTP Client | Attack scripts HTTP calls |
| pytest | 8.2.2 | Testing | Test runner |
| pytest-flask | 1.3.0 | Testing | Flask test client |
| pytest-cov | 5.0.0 | Testing | Code coverage reporting |
| httpretty | 1.1.4 | Testing | HTTP request mocking |
| colorama | 0.4.6 | Terminal UI | Coloured terminal output |
| click | 8.1.7 | Terminal UI | CLI utilities |
| tabulate | 0.9.0 | Terminal UI | Table formatting |
