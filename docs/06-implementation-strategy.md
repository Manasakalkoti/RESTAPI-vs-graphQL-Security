# Implementation Strategy

This document describes the code design decisions, patterns, and conventions used throughout
the project.

---

## Core Design Principle: Dual-Mode APIs

Each API is built with a `SECURE_MODE` flag. When the flag is off, the vulnerable version of
every handler runs. When it is on, the secured version runs. This allows:

- Attack scripts to run against the vulnerable API by setting `SECURE_MODE=false`.
- Security tests to run against the hardened API by setting `SECURE_MODE=true`.
- A direct comparison of the same endpoint in both states.

```python
import os
SECURE_MODE = os.getenv("SECURE_MODE", "false").lower() == "true"
```

---

## REST API Architecture

### Directory Layout

```
src/rest_api/
├── app.py                          # Flask app factory, route registration
├── models.py                       # SQLAlchemy model imports
├── routes/
│   ├── __init__.py
│   ├── users.py                    # /api/users/* endpoints
│   └── orders.py                   # /api/orders/* endpoints
├── middleware/
│   ├── __init__.py
│   └── auth.py                     # JWT validation decorator
└── security/
    ├── __init__.py
    ├── bola_protection.py          # Ownership check helper
    ├── mass_assignment_protection.py  # Allowlist filter function
    └── data_exposure_protection.py    # Marshmallow public schemas
```

### Request Lifecycle (Secured)

```
HTTP Request
    │
    ▼
auth.py middleware  ── JWT invalid ──► 401 Unauthorized
    │
    ▼
Route Handler
    │
    ├─ (PUT) mass_assignment_protection.py  ── filters input allowlist
    │
    ├─ (GET) bola_protection.py             ── ownership check added to query
    │
    ▼
SQLAlchemy Query
    │
    ▼
data_exposure_protection.py  ── Marshmallow public schema serialises response
    │
    ▼
HTTP Response (safe public fields only)
```

### Authentication Decorator

```python
from functools import wraps
from flask import request, g
import jwt, os

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        try:
            payload = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
            g.current_user_id = payload["user_id"]
        except jwt.InvalidTokenError:
            return {"error": "Unauthorized"}, 401
        return f(*args, **kwargs)
    return decorated
```

---

## GraphQL API Architecture

### Directory Layout

```
src/graphql_api/
├── app.py                          # Flask + Strawberry app factory
├── schema.py                       # Type definitions and root Query/Mutation
├── resolvers/
│   ├── __init__.py
│   └── user_resolver.py            # Resolver functions
└── security/
    ├── __init__.py
    ├── introspection_protection.py # Middleware to block __schema
    ├── depth_limit_protection.py   # AST depth counter
    └── complexity_protection.py    # AST cost calculator
```

### Request Lifecycle (Secured)

```
HTTP POST /graphql
    │
    ▼
introspection_protection.py  ── __schema/__type field ──► 403 Forbidden
    │
    ▼
depth_limit_protection.py    ── depth > 5 ──► 400 Bad Request
    │
    ▼
complexity_protection.py     ── cost > 100 ──► 400 Bad Request
    │
    ▼
Strawberry Resolver execution
    │
    ▼
HTTP Response
```

### GraphQL Schema Design

The schema includes a circular relationship between User and Post to enable the Depth DoS
demonstration:

```python
import strawberry
from typing import List, Optional

@strawberry.type
class Post:
    id: int
    title: str
    content: str
    author: Optional["User"] = None   # circular reference

@strawberry.type
class User:
    id: int
    username: str
    email: str
    bio: Optional[str]
    posts: List[Post]                  # circular reference

@strawberry.type
class Query:
    @strawberry.field
    def user(self, id: int) -> Optional[User]:
        return resolve_user(id)

    @strawberry.field
    def users(self) -> List[User]:
        return resolve_users()
```

---

## Shared Common Layer

### Database Setup (`src/common/database.py`)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///lab.db")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass
```

### Data Models (`src/common/models.py`)

Intentionally designed with both "safe" and "dangerous" fields to make all 6 vulnerabilities
demonstrable:

```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)   # dangerous: not in public schema
    is_admin = Column(Boolean, default=False)              # dangerous: mass assignment target
    bio = Column(String(500))
    reset_token = Column(String(256))                      # dangerous: not in public schema
    posts = relationship("Post", back_populates="author")  # circular: depth DoS enabler
```

---

## Attack Script Design

All attack scripts follow a consistent structure:

```python
# attacks/rest/bola_attack.py

BASE_URL = "http://localhost:5000"   # hardcoded to localhost — never external

def authenticate(username, password):
    """Get a valid JWT for the attacker's own account."""
    ...

def attack(token):
    """Cycle through IDs and collect unauthorised records."""
    results = []
    for order_id in range(1, 101):
        resp = requests.get(
            f"{BASE_URL}/api/orders/{order_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        if resp.status_code == 200:
            results.append(resp.json())
    return results

if __name__ == "__main__":
    token = authenticate("attacker", "password")
    stolen = attack(token)
    print(f"Accessed {len(stolen)} unauthorised records")
```

---

## Conventions

| Convention | Rule |
|-----------|------|
| Secrets | Never hardcoded — always from `.env` via `python-dotenv` |
| Error messages | Generic — never reveal internal field names or stack traces |
| HTTP status codes | 404 when resource not found OR not owned (prevents existence leakage) |
| Logging | Request logs include user_id and operation name, not full query bodies |
| Tests | Each test file covers one API × one mode (vulnerable or secured) |

---

## Running Both APIs Simultaneously

Both APIs share the same SQLite database file but run on different ports:

```bash
# Terminal 1
SECURE_MODE=false python src/rest_api/app.py      # port 5000, vulnerable

# Terminal 2
SECURE_MODE=false python src/graphql_api/app.py   # port 5001, vulnerable

# Terminal 3
bash scripts/run_attack_simulation.sh              # run all 6 attacks
```
