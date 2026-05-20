# Project Summary

## What This Project Is

This is a security research and demonstration lab that compares two modern API architectures —
**REST API** and **GraphQL API** — from a security perspective. Both APIs are built, attacked,
and defended in a controlled local environment so that every vulnerability and its corresponding
defence mechanism can be observed, tested, and understood clearly.

The project does not just explain security concepts in theory. It actually builds the vulnerable
systems, writes real attack scripts that exploit them, then applies defences and proves through
automated tests that every attack is blocked.

---

## The Problem This Project Solves

REST APIs and GraphQL APIs are the two most widely used approaches for building backends
today. Each one has a completely different internal structure, and because of those structural
differences, each one is vulnerable to a different class of attacks.

Most developers know how to build these APIs but are unaware of the specific ways they can
be exploited. This project makes those vulnerabilities visible and tangible by demonstrating
them live, and then shows exactly what code change is needed to fix each one.

---

## The Six Vulnerabilities Demonstrated

### REST API Vulnerabilities (3)

**1. BOLA / IDOR — Broken Object Level Authorization**
REST APIs use predictable numeric IDs in URLs such as `/api/orders/1001`. A logged-in
attacker simply changes the number to access records belonging to other users. The server
checks that the user is authenticated but never checks whether they actually own the resource
being requested. In this project, Alice logs in and accesses Bob and Charlie's orders by
cycling through IDs 1 to 12. Seven unauthorised records are returned without any error.

**2. Mass Assignment**
Modern web frameworks can automatically map every field in an incoming JSON request body
directly to database columns. An attacker intercepts a normal profile update request and adds
a hidden field — `is_admin: true` — that was never shown in the user interface. Because the
server accepts all incoming fields blindly, the `is_admin` flag is saved to the database and
the attacker gains admin privileges without any special access.

**3. Excessive Data Exposure**
The server returns the full database object in every API response, including sensitive fields
that the frontend never displays. An attacker opens the browser's Network tab and reads
`password_hash`, `reset_token`, `internal_notes`, and `is_admin` directly from the raw JSON
response. The frontend hides these fields visually but the data has already been delivered
to the client.

---

### GraphQL API Vulnerabilities (3)

**4. Introspection Abuse — The Map Maker**
GraphQL has a built-in feature called Introspection that lets anyone ask the server to describe
its own schema. By sending a single `__schema` query, an attacker receives a complete
blueprint of the entire API — every type, field, query, mutation, and relationship — without
needing access to the source code. This gives attackers the exact field names and hidden
operations they need to plan further attacks.

**5. Depth / Circular DoS — The Never-Ending Loop**
GraphQL schemas often contain circular relationships such as User → Posts → Author → Posts
→ Author. An attacker sends a single deeply nested query that follows this circular chain 8, 10,
or 20 levels deep. For each level the server performs multiple database lookups. A single
request at 15 or more levels can exhaust all server CPU and RAM, making the server
unresponsive to every other user. No authentication is required and no flood of requests is
needed — one query is enough.

**6. Alias / Batching Attack — The Machine Gun**
GraphQL allows multiple operations to be packed into a single HTTP request using aliases.
An attacker uses this to send 50 login attempts — each with a different password — inside
one HTTP request. To the server's rate limiter this looks like one request. Internally the
server processes all 50 operations individually. The correct password is found at attempt 49
and a valid token is returned. Standard rate limiting is completely bypassed.

---

## The Six Security Mechanisms Implemented

### REST API Defences

**Defence 1 — BOLA / IDOR Protection**
The database query adds an ownership condition. Instead of searching for an order by ID
alone, the query searches for an order that matches both the requested ID and the currently
logged-in user's ID. If the order exists but belongs to someone else, the server returns 404
Not Found — the same response as if the record did not exist at all, giving the attacker no
information about whether the record exists.

**Defence 2 — Mass Assignment Protection**
An explicit allowlist defines which fields a client is permitted to update — only `username`,
`email`, and `bio`. When a PUT request arrives, the server extracts only the fields on the
allowlist and ignores everything else. The injected `is_admin` field is silently discarded and
never reaches the database.

**Defence 3 — Excessive Data Exposure Protection**
A Marshmallow schema defines a safe public representation of each model. The `PublicUserSchema`
includes only `id`, `username`, `email`, and `bio`. The `PublicOrderSchema` includes only
`id`, `item_name`, and `amount`. Before any response is sent, the database object is
serialised through this schema. Sensitive fields — `password_hash`, `reset_token`,
`internal_notes`, `is_admin` — are excluded at the serialisation layer and never leave the
server.

### GraphQL API Defences

**Defence 4 — Introspection Protection**
An environment variable `DISABLE_INTROSPECTION=true` is set in production. A
`before_request` middleware checks every incoming GraphQL request for the `__schema` or
`__type` keywords. If either is found and introspection is disabled, the server returns a 400
error with a clear message. Normal business queries are completely unaffected.

**Defence 5 — Query Depth Limit**
Before any query reaches the resolvers, a validator parses the query string into an AST
(Abstract Syntax Tree) and walks it to measure the maximum nesting depth. The project
enforces a maximum depth of 5 levels. The 8-level attack query is rejected immediately with
a 400 error before a single database call is made. The response time drops from 0.024 seconds
to 0.007 seconds — the server does no work at all for the rejected query.

**Defence 6 — Query Complexity Budget**
Each field type is assigned a cost — `login` mutation costs 20, list fields cost 10, object
fields cost 5. When a request arrives, the server sums the total cost of all operations including
all aliases. The maximum budget is 100. Fifty aliased `login` operations cost 50 × 20 = 1,000,
which far exceeds the budget. The entire batch is rejected with a 400 error before any login
attempt is processed.

---

## How the Project Is Structured

```
RESTAPI-vs-graphQL-Security/
├── src/
│   ├── common/            Database models, JWT auth, seed data — shared by both APIs
│   ├── rest_api/          Flask REST API with vulnerable + secured modes
│   ├── graphql_api/       Strawberry GraphQL API with vulnerable + secured modes
│   └── dashboard/         Web dashboard and terminal menu for live demo
├── attacks/
│   ├── rest/              3 attack scripts targeting REST endpoints
│   └── graphql/           3 attack scripts targeting GraphQL endpoint
├── tests/                 33 automated tests covering all 6 attacks in both modes
├── docs/                  All project documentation
├── config/                Environment configuration files
└── scripts/               Setup and simulation shell scripts
```

Both APIs share the same SQLite database and the same data models. A single environment
variable `SECURE_MODE=false` runs the vulnerable version, `SECURE_MODE=true` runs the
secured version. This makes the before-and-after comparison direct and unambiguous.

---

## Technology Used

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Python | 3.9.6 |
| REST Framework | Flask | 3.0.3 |
| GraphQL Framework | Strawberry | 0.235.1 |
| GraphQL AST | graphql-core | 3.2.3 |
| ORM | SQLAlchemy | 2.0.30 |
| Database | SQLite | 3.39.5 |
| Authentication | PyJWT | 2.8.0 |
| Password Hashing | bcrypt | 4.1.3 |
| Response Filtering | marshmallow | 3.21.3 |
| Environment Config | python-dotenv | 1.0.1 |
| HTTP Client | requests | 2.32.3 |
| Testing | pytest | 8.2.2 |
| Coverage | pytest-cov | 5.0.0 |
| Terminal Colors | colorama | 0.4.6 |
| Dashboard | HTML + CSS + JS | — |

---

## Why Tests Are Conducted

### The Problem with Manual Testing Alone

The six attack scripts in the `attacks/` folder are effective live demonstrations, but they
depend on three external processes running simultaneously — the REST API server, the GraphQL
API server, and the correct environment variable being set. If any server is not running, or
if it was started with the wrong mode, the attack script either fails silently or returns
misleading output. There is no automatic way to know whether the result was caused by the
defence working correctly or simply by the server being unavailable.

Manual runs are also not repeatable in a controlled way. Two runs of the same attack script
on a live server can produce different results if the database state has changed, if a
previous test already escalated a user to admin, or if a previous attack left the server in
an unexpected state. Each manual run is a snapshot of one moment in time, not a proof.

The automated test suite solves all of these problems.

---

### Why Automated Tests

**1. No server required.**
Every test uses Flask's built-in test client, which calls route handlers directly inside the
same Python process. The test creates the app, sends an HTTP request through the test client,
and receives the response — all without any network socket, port, or background process. This
means the entire suite of 33 tests runs with a single command (`pytest tests/ -v`) and
completes in a few seconds regardless of what is or is not running on the machine.

**2. Isolated, deterministic state.**
Every test session uses a separate test database (`test_lab.db`). Before any test runs, the
conftest.py fixture drops all tables and recreates them from scratch, then seeds exactly the
data the tests need: alice with orders 1–3 and bob with orders 4–5. This means every test
starts from the same known state. It is impossible for one test to corrupt the data seen by
the next test.

**3. A repeatable, verifiable proof.**
The test suite is not documentation — it is executable proof. When all 33 tests pass, it
means the vulnerable mode exposes exactly the vulnerabilities claimed, and the secured mode
blocks exactly the attacks claimed. This proof can be regenerated at any time by anyone who
clones the repository. It does not depend on trust or on reading the code carefully.

---

### Why Two Sets of Tests: Vulnerable AND Secured

This is the most important design decision in the test suite. Every vulnerability is tested
twice — once against the vulnerable API and once against the secured API.

**Testing the vulnerable mode proves the exploit is real.**
It is easy to claim that a vulnerability exists. It is much harder to demonstrate that it
actually works. The vulnerable-mode tests send exactly the same payloads that a real attacker
would send and assert that the attack succeeds — that unauthorised data is returned, that
privilege escalation works, that the schema is exposed, that a nested query is accepted. If
these tests did not exist, there would be no automated proof that the vulnerable code is
actually exploitable, not just theoretically weak.

**Testing the secured mode proves the defence actually works.**
Writing a defence and then claiming it works is not sufficient. The secured-mode tests send
the same attack payloads against the secured API and assert that every attack is blocked with
the correct HTTP status code and a meaningful error message. If the defence has a bug — for
example, if the ownership check only works for some user IDs, or if the depth limit has an
off-by-one error — the secured-mode tests will catch it and fail. The tests do not just check
that the server returns an error. They check the specific status code (404 for BOLA, 400 for
GraphQL violations), confirm that sensitive fields are absent from responses, and verify that
the safe fields the client legitimately needs are still present.

**The before-and-after comparison is the core of the project.**
By running the vulnerable tests and the secured tests against the same codebase (switched
only by the `SECURE_MODE` flag), the test suite provides a direct, code-level comparison of
what changes when a defence is applied. Any reader can look at a failing test in the
vulnerable suite and a passing test in the secured suite and see exactly what the defence
does differently.

---

### What Each Test File Proves

#### `test_rest_vulnerabilities.py` — 8 tests

This file proves that the three REST vulnerabilities are genuinely exploitable on the
vulnerable API. It covers:

- **BOLA / IDOR**: Alice's token is used to request bob's orders (IDs 4 and 5). Both requests
  return HTTP 200 with full order data including `internal_notes`. The test confirms that the
  server does not check ownership at all — it returns any order to any authenticated user.

- **Mass Assignment**: A PUT request to Alice's profile includes the hidden field
  `"is_admin": True`. After the request, the test reads Alice's record from the database
  directly and asserts that `is_admin` is now `True`. The test also confirms that unexpected
  extra fields sent in the request are written to the database.

- **Excessive Data Exposure**: The `/api/users/profile` endpoint is called and the response
  JSON is inspected. The test asserts that `password_hash`, `reset_token`, `internal_notes`,
  and `is_admin` are all present in the response — fields that the frontend would never
  display but that are delivered to the client in full.

#### `test_rest_security.py` — 9 tests

This file proves that all three REST defences block the same attacks.

- **BOLA defence**: Alice requests bob's orders. Both return HTTP 404 — the same response as
  a non-existent record, giving the attacker no information about whether the record exists.
  Alice's own orders still return 200, confirming the defence does not break legitimate access.
  The response no longer contains `internal_notes`.

- **Mass Assignment defence**: The same `is_admin: True` payload is sent. After the request,
  Alice's `is_admin` is still `False` in the database. The test also confirms that a
  legitimate field in the payload (`bio`) was still updated correctly — the defence blocks
  the injected field without breaking the normal update.

- **Data Exposure defence**: The profile response now contains only `id`, `username`, `email`,
  and `bio`. The sensitive fields (`password_hash`, `reset_token`, `internal_notes`,
  `is_admin`) are completely absent. The test checks both that harmful fields are missing and
  that safe fields are present.

#### `test_graphql_vulnerabilities.py` — 7 tests

This file proves that the three GraphQL vulnerabilities are genuine on the vulnerable API.

- **Introspection Abuse**: A `__schema` introspection query returns HTTP 200 and the response
  contains type names from the schema (`UserType`, `PostType`, `OrderType`). A `__type` query
  for the User type returns all field names. The test confirms the full schema is openly
  accessible without authentication.

- **Depth / Circular DoS**: An 8-level deeply nested circular query (`user → posts → author
  → posts → author → posts → author → username`) returns HTTP 200 and no error. The test
  confirms the server processes the query without any depth checking — it accepts work that
  could exhaust CPU and RAM on a production server.

- **Alias / Batching**: A request containing 10 aliased `login` mutations (a reduced version
  of the 50-alias attack for test speed) returns HTTP 200. The response contains all 10
  aliased results, proving the server processes every operation in the batch individually
  with no per-operation rate limiting.

#### `test_graphql_security.py` — 9 tests

This file proves that all three GraphQL defences stop the same attacks.

- **Introspection defence**: The `__schema` query returns HTTP 400. The error message
  explicitly mentions that introspection is disabled. A normal business query (`{ users { id
  username } }`) still returns HTTP 200, confirming the middleware only blocks introspection
  queries, not all GraphQL traffic.

- **Depth limit defence**: The 8-level nested query returns HTTP 400. The error message
  mentions "depth" and "5" (the maximum). A 3-level query (within the limit) still returns
  HTTP 200, confirming the depth check does not break normal queries.

- **Complexity budget defence**: The 50-alias batching attack returns HTTP 400. The error
  message mentions "complexity" and "100" (the budget). A single `login` mutation (cost 20,
  within the budget) still returns HTTP 200 with a valid token, confirming the defence does
  not break normal authentication.

---

### How the Test Infrastructure Works

The `tests/conftest.py` file sets up everything before a single test runs:

1. It sets `DATABASE_URL` and `JWT_SECRET` environment variables before any application
   module is imported, so the app uses the test database and a known secret key throughout.

2. It defines a `_seed_test_db()` function that drops all tables, recreates them, and inserts
   two users (alice and bob) with five orders between them. This function is called once per
   test session, giving every test the same starting data.

3. It defines four pytest fixtures: `vuln_rest`, `sec_rest`, `vuln_gql`, and `sec_gql`. Each
   fixture calls the application factory with `secure=False` or `secure=True` and returns a
   Flask test client. Tests receive whichever client they need as a parameter.

4. It defines `alice_token` and `bob_token` fixtures that generate valid JWT tokens for each
   user using the same `generate_token()` function the application uses in production. Tests
   that need an authenticated request pass the token as a Bearer header.

---

## Test Results

The project includes 33 automated tests across 4 test files. All 33 pass.

| Test File | What It Proves | Tests |
|-----------|---------------|-------|
| `test_rest_vulnerabilities.py` | All 3 REST attacks succeed on vulnerable API | 8 |
| `test_rest_security.py` | All 3 REST attacks are blocked on secured API | 9 |
| `test_graphql_vulnerabilities.py` | All 3 GraphQL attacks succeed on vulnerable API | 7 |
| `test_graphql_security.py` | All 3 GraphQL attacks are blocked on secured API | 9 |
| **Total** | | **33 passed** |

Tests run without any server — they use Flask's internal test client directly. This means
the test suite can be run at any time with a single command and does not depend on any
external process being active.

---

## Live Demo Results

### Vulnerable Mode — All 6 Attacks Succeeded

| Attack | What the attacker obtained |
|--------|--------------------------|
| BOLA / IDOR | 7 unauthorised orders from Bob and Charlie's accounts |
| Mass Assignment | `is_admin` escalated from False to True |
| Excessive Data Exposure | `password_hash`, `reset_token`, `internal_notes`, `is_admin` all visible |
| Introspection Abuse | Full API schema — 8 types, all fields, all mutations |
| Depth / Circular DoS | 8-level nested query accepted and processed in 0.024s |
| Alias / Batching | Password cracked at attempt 49 out of 50 in a single HTTP request |

### Secured Mode — All 6 Attacks Blocked

| Attack | Defence Response |
|--------|----------------|
| BOLA / IDOR | 404 Not Found for all of Bob and Charlie's orders |
| Mass Assignment | `is_admin` remained False, injected field discarded |
| Excessive Data Exposure | Only `id`, `username`, `email`, `bio` returned |
| Introspection Abuse | 400 — Introspection is disabled on this server |
| Depth / Circular DoS | 400 — Query depth 8 exceeds maximum allowed depth of 5 |
| Alias / Batching | 400 — Query complexity 1150 exceeds budget of 100 |

---

## Documentation Index

| File | Contents |
|------|---------|
| `docs/summary.md` | This file — full project overview |
| `docs/01-project-overview.md` | Goals, scope, architecture decisions, data model |
| `docs/02-rest-api-vulnerabilities.md` | Detailed explanation of all 3 REST vulnerabilities |
| `docs/03-graphql-vulnerabilities.md` | Detailed explanation of all 3 GraphQL vulnerabilities |
| `docs/04-security-mechanisms.md` | Code-level explanation of all 6 defences |
| `docs/05-attack-comparison.md` | Side-by-side REST vs GraphQL attack surface analysis |
| `docs/06-implementation-strategy.md` | Code design decisions and dual-mode architecture |
| `docs/07-testing-strategy.md` | Test plan, fixture setup, all test cases with code |
| `docs/setup.md` | Step-by-step environment setup and installation guide |
| `docs/commands.md` | All commands needed to run, test, and demo the project |
| `docs/dashboard-execution.md` | Step-by-step guide to run the web dashboard demo |
| `docs/techstack.md` | Every package explained — what it is, why used, where used |

---

## Key Takeaways

1. **Authentication is not the same as authorization.** Being logged in does not mean a user
   should access every resource. Every data access must verify ownership.

2. **Never trust all incoming fields.** Servers must explicitly define which fields they accept.
   Everything else must be discarded before it reaches the database.

3. **Only send what the client actually needs.** Responses must be filtered through a public
   schema. Sensitive fields must be excluded at the server, not hidden by the frontend.

4. **GraphQL introspection must be disabled in production.** Leaving it on gives attackers a
   free map of the entire backend before they make a single real request.

5. **Rate limiting alone is not enough for GraphQL.** A complexity budget that measures the
   actual workload of each request is required to stop alias and batching attacks.

6. **Depth limits are essential for any circular GraphQL schema.** A single deeply nested
   query can bring down a server. The fix is a pre-execution AST depth check that costs
   almost nothing.
