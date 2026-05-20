# Execution Plan — REST API vs GraphQL Security Lab

## Overview

This document is the authoritative delivery plan for the project. It breaks the work into six
sequential phases, each with clear goals, tasks, deliverables, and success criteria.

---

## Phase 1 — Project Setup

**Goal:** Establish a working development baseline with shared infrastructure.

### Tasks

| # | Task | Details |
|---|------|---------|
| 1.1 | Initialise virtual environment | `python3 -m venv venv`, install base packages |
| 1.2 | Configure environment files | `config/development.env`, `config/production.env` |
| 1.3 | Set up SQLAlchemy + SQLite | `src/common/database.py` — engine, session factory, Base |
| 1.4 | Define shared data models | User, Post, Order models with realistic fields |
| 1.5 | Implement JWT auth helper | `src/common/auth.py` — token generation, verification |
| 1.6 | Seed database with test data | Script to populate users, posts, orders |
| 1.7 | Verify environment | Both API servers start, DB reachable, JWT round-trips |

### Deliverables
- Working venv with `requirements.txt` locked
- SQLite DB with seeded records
- Shared auth module used by both APIs

### Success Criteria
- `python src/rest_api/app.py` starts on port 5000 without errors
- `python src/graphql_api/app.py` starts on port 5001 without errors
- JWT encode/decode round-trip passes unit test

---

## Phase 2 — Vulnerable API Implementation

**Goal:** Build both APIs in their intentionally vulnerable state so attack scripts have a target.

### REST API — Vulnerable Endpoints

| Endpoint | Method | Vulnerability Introduced |
|----------|--------|--------------------------|
| `/api/users/register` | POST | No input filtering (Mass Assignment) |
| `/api/users/profile` | GET | Returns full DB object (Excessive Data Exposure) |
| `/api/orders/<id>` | GET | No ownership check (BOLA / IDOR) |
| `/api/users/<id>` | PUT | Accepts all fields blindly (Mass Assignment) |

### GraphQL API — Vulnerable Schema

| Feature | Vulnerability Introduced |
|---------|--------------------------|
| Introspection enabled unconditionally | Introspection Abuse |
| No query depth limit | Depth / Circular DoS |
| No query complexity budget | Alias / Batching Attack |

### Tasks

| # | Task |
|---|------|
| 2.1 | Build Flask REST app with vulnerable endpoints |
| 2.2 | Build Strawberry GraphQL schema (User, Post, Order types) |
| 2.3 | Add resolvers with circular relationships (User → Posts → Author → Posts) |
| 2.4 | Verify all 6 vulnerable behaviours are reproducible manually |

### Deliverables
- `src/rest_api/app.py` with 4+ vulnerable endpoints
- `src/graphql_api/app.py` with fully introspectable schema
- Manual verification notes for each vulnerability

---

## Phase 3 — Attack Simulation

**Goal:** Write reproducible attack scripts for all 6 vulnerabilities.

### Attack Scripts

| Script | Target | Attack Type |
|--------|--------|-------------|
| `attacks/rest/bola_attack.py` | `GET /api/orders/<id>` | BOLA / IDOR |
| `attacks/rest/mass_assignment_attack.py` | `PUT /api/users/<id>` | Mass Assignment |
| `attacks/rest/excessive_data_attack.py` | `GET /api/users/profile` | Excessive Data Exposure |
| `attacks/graphql/introspection_attack.py` | GraphQL endpoint | Introspection Abuse |
| `attacks/graphql/depth_dos_attack.py` | GraphQL endpoint | Depth / Circular DoS |
| `attacks/graphql/alias_batching_attack.py` | GraphQL endpoint | Alias / Batching |

### Tasks

| # | Task |
|---|------|
| 3.1 | Write BOLA attack — cycle IDs 1–50, print unauthorised records |
| 3.2 | Write Mass Assignment attack — inject `is_admin=true` into PUT request |
| 3.3 | Write Excessive Data attack — log all extra fields in response |
| 3.4 | Write Introspection attack — dump full schema using `__schema` query |
| 3.5 | Write Depth DoS attack — send 15-level nested query, measure CPU spike |
| 3.6 | Write Alias Batching attack — embed 50 login attempts in one request |
| 3.7 | Run all scripts against Phase 2 APIs, capture output as baseline |

### Deliverables
- 6 documented attack scripts with expected output
- Baseline attack output captured (before security is applied)

---

## Phase 4 — Security Implementation

**Goal:** Apply targeted defences that neutralise each attack without breaking normal usage.

### REST API Defences

| Defence | File | Mechanism |
|---------|------|-----------|
| BOLA / IDOR Protection | `src/rest_api/security/bola_protection.py` | Ownership check: resource.user_id == current_user.id |
| Mass Assignment Protection | `src/rest_api/security/mass_assignment_protection.py` | Allowlist filter — only `name`, `email`, `bio` accepted |
| Excessive Data Exposure | `src/rest_api/security/data_exposure_protection.py` | Serialise to safe public schema via Marshmallow |

### GraphQL API Defences

| Defence | File | Mechanism |
|---------|------|-----------|
| Introspection Protection | `src/graphql_api/security/introspection_protection.py` | Disable via env flag in production |
| Depth Limit Protection | `src/graphql_api/security/depth_limit_protection.py` | Reject queries with depth > 5 |
| Complexity Budget | `src/graphql_api/security/complexity_protection.py` | Reject queries with cost > 100 |

### Tasks

| # | Task |
|---|------|
| 4.1 | Implement and wire BOLA ownership check |
| 4.2 | Implement allowlist input filter for mass assignment |
| 4.3 | Create Marshmallow public schemas for all models |
| 4.4 | Add introspection toggle via `DISABLE_INTROSPECTION` env var |
| 4.5 | Write query depth validator middleware |
| 4.6 | Write query complexity calculator and enforce budget |
| 4.7 | Re-run all 6 attack scripts — each must now be blocked |

### Deliverables
- All 6 defences implemented and wired into the API handlers
- Attack scripts return 400/403 responses after hardening

---

## Phase 5 — Testing

**Goal:** Automated test coverage that verifies both vulnerable behaviour and secure behaviour.

### Test Files

| File | Coverage |
|------|----------|
| `tests/test_rest_vulnerabilities.py` | Confirms all 3 REST attacks succeed on vulnerable API |
| `tests/test_rest_security.py` | Confirms all 3 REST attacks fail on secured API |
| `tests/test_graphql_vulnerabilities.py` | Confirms all 3 GraphQL attacks succeed on vulnerable API |
| `tests/test_graphql_security.py` | Confirms all 3 GraphQL attacks fail on secured API |

### Tasks

| # | Task |
|---|------|
| 5.1 | Write pytest fixtures (test client, seeded DB, test JWT) |
| 5.2 | Write vulnerability-confirmation tests (expect 200 where attack succeeds) |
| 5.3 | Write security-confirmation tests (expect 400/403 where attack is blocked) |
| 5.4 | Run full suite, achieve >= 80% coverage |
| 5.5 | Add coverage report to CI output |

### Success Criteria
- All tests pass: `pytest tests/ -v` returns 0 failures
- Coverage >= 80%: `pytest --cov=src tests/`

---

## Phase 6 — Documentation

**Goal:** Finalise all markdown documentation files so the project is self-explanatory.

### Tasks

| # | Task |
|---|------|
| 6.1 | Complete `docs/01-project-overview.md` |
| 6.2 | Complete `docs/02-rest-api-vulnerabilities.md` |
| 6.3 | Complete `docs/03-graphql-vulnerabilities.md` |
| 6.4 | Complete `docs/04-security-mechanisms.md` |
| 6.5 | Complete `docs/05-attack-comparison.md` |
| 6.6 | Complete `docs/06-implementation-strategy.md` |
| 6.7 | Complete `docs/07-testing-strategy.md` |
| 6.8 | Complete `docs/08-future-enhancements.md` |
| 6.9 | Complete `docs/09-conclusion.md` |
| 6.10 | Review README for accuracy |

---

## Overall Timeline Estimate

| Phase | Estimated Effort |
|-------|-----------------|
| Phase 1 — Setup | 0.5 day |
| Phase 2 — Vulnerable APIs | 1.5 days |
| Phase 3 — Attack Simulation | 1 day |
| Phase 4 — Security Implementation | 1.5 days |
| Phase 5 — Testing | 1 day |
| Phase 6 — Documentation | 0.5 day |
| **Total** | **~6 days** |

---

## Risk Register

| Risk | Mitigation |
|------|-----------|
| SQLAlchemy circular relationship causes infinite loop | Use `lazy="select"` + depth limit before query execution |
| Attack scripts targeting external systems | All scripts hardcoded to `localhost` only |
| JWT secret exposed in config | Use `.env` gitignored file; never commit secrets |
| Strawberry version API breaking changes | Pin exact version in `requirements.txt` |
