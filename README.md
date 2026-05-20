# REST API vs GraphQL Security — Vulnerability Comparison & Defense Lab

A hands-on research and implementation project that demonstrates, simulates, and mitigates
real-world security vulnerabilities in both REST APIs and GraphQL APIs side by side.

---

## Project Purpose

Modern backends are built on either REST or GraphQL. Each architecture introduces a distinct
class of security weaknesses. This project builds both APIs against a shared database, exposes
them to controlled attack simulations, then hardens each one with targeted defences — making
the before/after contrast fully observable and testable.

---

## Vulnerabilities Covered

| API Type | Vulnerability | Nickname |
|----------|--------------|---------|
| GraphQL | Introspection Abuse | The Map Maker |
| GraphQL | Depth / Circular DoS | The Never-Ending Loop |
| GraphQL | Alias / Batching Attack | The Machine Gun |
| REST | BOLA / IDOR | The Number Guesser |
| REST | Mass Assignment | The Hidden Field Trick |
| REST | Excessive Data Exposure | The TMI Response |

---

## Repository Layout

```
RESTAPI-vs-graphQL-Security/
├── src/
│   ├── rest_api/          # Vulnerable + secured Flask REST API
│   ├── graphql_api/       # Vulnerable + secured Strawberry GraphQL API
│   └── common/            # Shared DB models, JWT auth, helpers
├── attacks/
│   ├── rest/              # Attack scripts targeting REST endpoints
│   └── graphql/           # Attack scripts targeting GraphQL endpoint
├── tests/
│   ├── test_rest_*.py
│   └── test_graphql_*.py
├── docs/                  # All project documentation markdown files
├── config/                # Environment config files
├── scripts/               # Setup and simulation shell scripts
└── requirements.txt
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| REST Framework | Flask 3.x |
| GraphQL Framework | Strawberry-graphql |
| Database | SQLite (dev) / PostgreSQL (prod) |
| ORM | SQLAlchemy 2.x |
| Authentication | JWT via PyJWT |
| Input Validation | Marshmallow |
| Rate Limiting | Flask-Limiter |
| Query Depth Limiting | graphql-core |
| Testing | pytest + pytest-flask |
| Attack Simulation | requests |

---

## Quick Start

```bash
# 1. Clone and enter project
git clone <repo-url>
cd RESTAPI-vs-graphQL-Security

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp config/development.env .env

# 5. Run REST API
python src/rest_api/app.py

# 6. Run GraphQL API (separate terminal)
python src/graphql_api/app.py

# 7. Run attack simulations
bash scripts/run_attack_simulation.sh

# 8. Run test suite
pytest tests/ -v
```

---

## Documentation Index

| Document | Description |
|----------|-------------|
| [Project Overview](docs/01-project-overview.md) | Goals, scope, and architecture decisions |
| [REST API Vulnerabilities](docs/02-rest-api-vulnerabilities.md) | BOLA, Mass Assignment, Excessive Data Exposure |
| [GraphQL Vulnerabilities](docs/03-graphql-vulnerabilities.md) | Introspection Abuse, Depth DoS, Alias Batching |
| [Security Mechanisms](docs/04-security-mechanisms.md) | All defensive implementations explained |
| [Attack Comparison](docs/05-attack-comparison.md) | Side-by-side REST vs GraphQL attack analysis |
| [Implementation Strategy](docs/06-implementation-strategy.md) | Code design decisions and patterns |
| [Testing Strategy](docs/07-testing-strategy.md) | Test plan, coverage targets, and tooling |
| [Future Enhancements](docs/08-future-enhancements.md) | Roadmap for additional features |
| [Conclusion](docs/09-conclusion.md) | Key findings and lessons learned |
| [Execution Plan](EXECUTION_PLAN.md) | Phased delivery roadmap |

---

## Execution Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 — Setup | Project scaffolding, DB, auth baseline | Planned |
| 2 — Implementation | Build vulnerable REST + GraphQL APIs | Planned |
| 3 — Attack Simulation | Write and run all 6 attack scripts | Planned |
| 4 — Security Implementation | Apply all 6 defences | Planned |
| 5 — Testing | pytest suite, coverage report | Planned |
| 6 — Documentation | Finalise all markdown docs | Planned |

---

## License

MIT — for educational and research purposes only. Do not run attack scripts against systems
you do not own or have explicit permission to test.
