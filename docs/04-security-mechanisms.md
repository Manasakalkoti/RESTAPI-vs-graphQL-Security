# Security Mechanisms

This document describes each defence implemented in the project — what it does, how it works
in code, and why it stops the corresponding attack.

---

## GraphQL Defences

### 1. Introspection Protection

**Stops:** Introspection Abuse (Map Maker)

#### Mechanism

The GraphQL server checks an environment variable before processing any request. If the
variable `DISABLE_INTROSPECTION=true` is set (as it would be in production), any query
containing `__schema` or `__type` fields is rejected before reaching the resolvers.

Normal queries (fetching users, posts, orders) are unaffected.

#### Environment-Based Control

```
Development (.env):
    DISABLE_INTROSPECTION=false     ← introspection ON for developer tooling

Production (.env.production):
    DISABLE_INTROSPECTION=true      ← introspection OFF for public users
```

#### Code Pattern

```python
import os
from graphql import GraphQLError

def introspection_middleware(next_fn, root, info, **kwargs):
    if os.getenv("DISABLE_INTROSPECTION", "false").lower() == "true":
        field_name = info.field_name
        if field_name.startswith("__"):
            raise GraphQLError(
                "Introspection is disabled on this server."
            )
    return next_fn(root, info, **kwargs)
```

#### Why This Works

- Removes the attacker's ability to map the backend for free.
- Developers retain access in their local environments.
- Normal business operations are completely unaffected.

---

### 2. Query Depth Limit Protection

**Stops:** Depth / Circular DoS (Never-Ending Loop)

#### Mechanism

Before any query reaches the database, a validation step walks the query's AST (Abstract
Syntax Tree) and counts the maximum nesting depth. If depth exceeds the configured limit
(default: 5), the query is rejected immediately.

#### Maximum Allowed Depth

| Use Case | Max Depth |
|----------|----------|
| Normal queries (user → posts) | 2–3 levels |
| Complex legitimate queries | 4–5 levels |
| Project-configured limit | **5** |
| Typical DoS attack | 10–50 levels |

#### Code Pattern

```python
from graphql import parse, validate
from graphql.validation import NoSchemaIntrospectionCustomRule

def check_query_depth(query_string: str, max_depth: int = 5) -> int:
    ast = parse(query_string)
    depth = _calculate_depth(ast.definitions[0], current_depth=0)
    if depth > max_depth:
        raise ValueError(
            f"Query depth {depth} exceeds maximum allowed depth of {max_depth}."
        )
    return depth
```

#### Why This Works

- The query is analysed before execution — no database calls are made.
- Deep recursive trees are caught at the validation layer.
- Legitimate deeply-nested queries are rare; limit of 5 covers normal use cases.
- CPU and memory are never consumed for oversized queries.

---

### 3. Query Complexity Budget

**Stops:** Alias / Batching Attack (Machine Gun)

#### Mechanism

The server assigns a cost weight to each field type in the schema:

| Operation Type | Cost |
|---------------|------|
| Simple scalar field | 1 |
| Object field (one DB lookup) | 5 |
| List field (many DB lookups) | 10 |
| Authentication mutation (login) | 20 |

When a query arrives, the server calculates the total cost of all operations — including all
aliases. If the total exceeds the budget (default: 100), the request is rejected.

#### How Alias Batching Is Caught

A single `login` mutation costs 20.
Fifty aliased `login` mutations cost 50 × 20 = **1,000** — far above the budget of 100.

The server rejects the request even though it is technically one HTTP request.

#### Code Pattern

```python
FIELD_COSTS = {
    "login": 20,
    "users": 10,
    "posts": 10,
    "user": 5,
    "post": 5,
}

def calculate_complexity(query_string: str, max_complexity: int = 100) -> int:
    ast = parse(query_string)
    total = _sum_field_costs(ast.definitions[0], FIELD_COSTS)
    if total > max_complexity:
        raise ValueError(
            f"Query complexity {total} exceeds maximum budget of {max_complexity}."
        )
    return total
```

#### Why This Works

- Rate limiting by HTTP request count is bypassed by batching — complexity limits are not.
- The server measures *actual workload* rather than *visible traffic*.
- A legitimate complex query rarely exceeds 100; 50 aliased logins always will.

---

## REST API Defences

### 4. BOLA / IDOR Protection (Ownership Check)

**Stops:** BOLA / IDOR (Number Guesser)

#### Mechanism

Instead of searching for a resource by ID alone, the server adds an ownership condition to
every query: the resource's `user_id` must match the authenticated user's ID.

Both conditions must be true simultaneously — existence AND ownership.

#### Code Pattern

```python
@app.route("/api/orders/<int:order_id>")
@require_auth
def get_order(order_id):
    order = db.session.execute(
        db.select(Order).where(
            Order.id == order_id,
            Order.user_id == current_user.id     # ownership check
        )
    ).scalar_one_or_none()

    if not order:
        return {"error": "Not found"}, 404       # same error for not-found and not-owned
    return safe_order_schema.dump(order), 200
```

#### Why Returning 404 Instead of 403

Returning `403 Forbidden` tells the attacker the resource exists but they cannot access it.
Returning `404 Not Found` gives no information — the attacker cannot tell if the record
exists at all. This is called "security through obscurity of existence" and reduces
information leakage.

#### Why This Works

- Modifying the ID in the URL no longer helps — the ownership condition eliminates all
  records belonging to other users.
- The query searches by `(id AND user_id)` — an attacker would need to guess both.

---

### 5. Mass Assignment Protection (Allowlist Filter)

**Stops:** Mass Assignment (Hidden Field Trick)

#### Mechanism

The server defines an explicit allowlist of fields that are permitted to be updated. When a
request arrives, only fields on the allowlist are extracted and applied. All other fields —
including attacker-injected ones — are silently discarded.

#### Allowed vs Protected Fields

| Field | Allowed in PUT /users | Reason |
|-------|----------------------|--------|
| `name` | Yes | User-visible profile field |
| `email` | Yes | User-visible profile field |
| `bio` | Yes | User-visible profile field |
| `is_admin` | **No** | Privilege escalation risk |
| `password_hash` | **No** | Must go through password change flow |
| `created_at` | **No** | Internal timestamp |
| `reset_token` | **No** | Internal security token |

#### Code Pattern

```python
ALLOWED_UPDATE_FIELDS = {"name", "email", "bio"}

@app.route("/api/users/<int:user_id>", methods=["PUT"])
@require_auth
def update_user(user_id):
    data = request.json
    safe_data = {
        key: value
        for key, value in data.items()
        if key in ALLOWED_UPDATE_FIELDS      # only allowlisted fields pass
    }
    user = db.session.get(User, user_id)
    for key, value in safe_data.items():
        setattr(user, key, value)
    db.session.commit()
    return {"message": "Updated"}, 200
```

#### Why This Works

- Attacker-injected fields (`is_admin`, `role`, `password_hash`) never reach the ORM.
- The allowlist is defined in server code — the attacker cannot change it.
- New database columns added later do not become vulnerable automatically.

---

### 6. Excessive Data Exposure Protection (Public Schema)

**Stops:** Excessive Data Exposure (TMI Response)

#### Mechanism

A Marshmallow schema defines a limited "public view" of each model. Only fields in this schema
are serialised into the response. Sensitive fields are excluded at the serialisation layer and
never leave the server.

#### Public Schema vs Database Schema

| Field | In DB | In Public Schema |
|-------|-------|-----------------|
| `id` | Yes | Yes (needed for references) |
| `username` | Yes | Yes |
| `email` | Yes | Yes |
| `bio` | Yes | Yes |
| `password_hash` | Yes | **No** |
| `is_admin` | Yes | **No** |
| `reset_token` | Yes | **No** |
| `internal_notes` | Yes | **No** |
| `created_at` | Yes | **No** |

#### Code Pattern

```python
from marshmallow import Schema, fields

class PublicUserSchema(Schema):
    id = fields.Int()
    username = fields.Str()
    email = fields.Str()
    bio = fields.Str()
    # password_hash, is_admin, reset_token intentionally omitted

public_user_schema = PublicUserSchema()

@app.route("/api/users/profile")
@require_auth
def get_profile():
    user = db.session.get(User, current_user.id)
    return public_user_schema.dump(user), 200   # only safe fields serialised
```

#### Why This Works

- Sensitive fields are excluded before the response is built — they are never in the response
  object at all.
- No attacker-visible fields can be found in the Network tab.
- Adding new sensitive DB columns does not automatically expose them (safe-by-default).

---

## Defence Summary

| Attack | Defence | Enforcement Layer |
|--------|---------|------------------|
| Introspection Abuse | Disable in production via env var | Request middleware |
| Depth DoS | Query depth limit (max 5) | AST validation before execution |
| Alias Batching | Query complexity budget (max 100) | AST cost calculation before execution |
| BOLA / IDOR | Ownership check in DB query | Route handler |
| Mass Assignment | Allowlist input filter | Route handler |
| Excessive Data Exposure | Public Marshmallow schema | Serialisation layer |
