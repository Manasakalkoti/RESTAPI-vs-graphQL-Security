# Project Overview

## What This Project Is

This project is a security research and implementation lab that places REST API and GraphQL
API architectures side by side to study, demonstrate, and defend against their respective
vulnerability classes.

Each API is built in two states:
- **Vulnerable** — intentionally insecure to allow attack simulation
- **Secured** — hardened with targeted defences that neutralise each attack

The project makes the security contrast directly observable through attack scripts and an
automated test suite.

---

## Goals

1. Understand the structural differences between REST and GraphQL that create different
   attack surfaces.
2. Implement all 6 documented vulnerabilities in a controlled lab environment.
3. Write reproducible attack scripts that prove each vulnerability is exploitable.
4. Apply targeted defences and prove via tests that each attack is now blocked.
5. Produce clear, reusable documentation for each vulnerability and defence.

---

## Scope

### In Scope

| Area | Details |
|------|---------|
| GraphQL Vulnerabilities | Introspection Abuse, Depth/Circular DoS, Alias/Batching Attack |
| REST Vulnerabilities | BOLA/IDOR, Mass Assignment, Excessive Data Exposure |
| Security Mechanisms | All 6 corresponding defences |
| Attack Simulation | Python-based attack scripts against localhost only |
| Testing | pytest suite verifying both vulnerable and secured behaviour |

### Out of Scope

- SQL Injection, XSS, CSRF (these are application-level concerns not specific to REST/GraphQL architecture)
- Network-level attacks
- Authentication bypass (JWT is assumed to work correctly; focus is on authorisation and data-layer vulnerabilities)
- Production deployment

---

## Architecture Decision: Why Both APIs Share One Database

Both the REST and GraphQL APIs operate against the same SQLite database and the same
SQLAlchemy models. This design ensures:

- Vulnerabilities are compared under identical data conditions
- The same seed data is available to both attack scripts
- Defensive code can be compared directly without confounding data differences

---

## Data Model

```
User
├── id (integer, primary key)
├── username (string, unique)
├── email (string, unique)
├── password_hash (string)        ← never exposed in public schema
├── is_admin (boolean, default=False)  ← protected from mass assignment
├── bio (string)
└── posts (relationship → Post[])

Post
├── id (integer, primary key)
├── title (string)
├── content (string)
├── author_id (FK → User.id)
└── author (relationship → User)   ← circular: used in depth DoS demo

Order
├── id (integer, primary key)
├── user_id (FK → User.id)         ← ownership field: used in BOLA demo
├── item_name (string)
├── amount (float)
└── internal_notes (string)        ← never exposed in public schema
```

---

## Project Structure

```
RESTAPI-vs-graphQL-Security/
├── src/
│   ├── rest_api/          # Flask REST API (vulnerable + secured modes)
│   │   ├── app.py
│   │   ├── models.py
│   │   ├── routes/
│   │   ├── middleware/
│   │   └── security/
│   ├── graphql_api/       # Strawberry GraphQL API (vulnerable + secured modes)
│   │   ├── app.py
│   │   ├── schema.py
│   │   ├── resolvers/
│   │   └── security/
│   └── common/            # Shared: DB engine, models, JWT auth
├── attacks/               # One attack script per vulnerability
├── tests/                 # pytest test suite
├── docs/                  # All markdown documentation
├── config/                # .env files
├── scripts/               # Shell scripts for setup and simulation
└── requirements.txt
```

---

## Tech Stack Summary

| Component | Choice | Reason |
|-----------|--------|--------|
| Language | Python 3.11 | Mature security ecosystem, readable attack scripts |
| REST Framework | Flask | Minimal, explicit — makes vulnerabilities visible in code |
| GraphQL Framework | Strawberry | Modern, type-safe, good depth/complexity plugin support |
| ORM | SQLAlchemy 2.x | Clear ownership queries; no magic bulk saves |
| Auth | PyJWT | Industry standard, auditable |
| Validation | Marshmallow | Explicit schema definitions for safe public serialisation |
| Rate Limiting | Flask-Limiter | Used in complexity budget middleware |
| Testing | pytest + pytest-flask | Standard, flexible, good coverage reporting |

---

## How to Run the Lab

See [README.md](../README.md) for the quick-start guide and
[EXECUTION_PLAN.md](../EXECUTION_PLAN.md) for the full phased delivery plan.
