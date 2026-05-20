# GraphQL Vulnerabilities

GraphQL's power comes from client-driven queries: clients decide exactly what data they want
and how deeply to follow relationships. This same flexibility creates a distinct class of
server-side vulnerabilities that do not exist in REST APIs.

This project demonstrates three GraphQL vulnerabilities: Introspection Abuse, Depth/Circular
DoS, and Alias/Batching Attack.

---

## 1. Introspection Abuse — "The Map Maker"

### What It Is

Introspection is a built-in GraphQL feature that lets anyone ask the server to describe its own
schema. It returns a complete inventory of:
- All available types, queries, and mutations
- Field names and their data types
- Relationships between objects
- Hidden admin functions and internal fields

This is designed for developer tooling (e.g. GraphiQL, Postman) but is often left enabled in
production.

### How the Attack Works

The attacker sends a single special query using the reserved `__schema` or `__type` keywords:

```graphql
query IntrospectionQuery {
  __schema {
    types {
      name
      fields {
        name
        type {
          name
        }
      }
    }
  }
}
```

The server responds with the complete API blueprint — every query, mutation, field name, and
type relationship in the entire backend.

The attacker does not need the source code. They now have a complete map of the API,
including:
- Hidden admin queries not linked from the UI
- Internal field names that reveal database schema
- Mutation names that hint at privileged operations (e.g. `promoteToAdmin`, `deleteUser`)

### Why This Is Dangerous

- Gives attackers a head start for chaining further attacks.
- Reveals field names needed for Mass Assignment or BOLA attacks.
- Exposes hidden admin mutations that are not documented publicly.
- No authentication required by default.

### Vulnerable Configuration

```python
# VULNERABLE — introspection enabled unconditionally
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    # introspection defaults to True
)
```

### Attack Script

See `attacks/graphql/introspection_attack.py` — sends the `__schema` query and prints a
formatted tree of all discovered types and fields.

---

## 2. Depth / Circular DoS — "The Never-Ending Loop"

### What It Is

GraphQL schemas frequently contain circular relationships. For example:

```
User → posts → Post → author → User → posts → Post → author → ...
```

A legitimate query might request one or two levels deep. An attacker deliberately requests
many levels — 10, 20, or 50 — inside a single HTTP request.

### How the Attack Works

```graphql
query DepthAttack {
  user(id: 1) {
    posts {
      author {
        posts {
          author {
            posts {
              author {
                posts {
                  author {
                    username   # 8 levels deep — server processes each step
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

For each level, the server must:
1. Execute a database query
2. Load the related objects into memory
3. Begin processing the next level

A single request with 15+ levels can force thousands of database round-trips and consume
gigabytes of memory. The server becomes unresponsive to all other users.

The attacker does not need to send thousands of requests. **One query is enough.**

### Why This Is Dangerous

- Denial of Service from a single unauthenticated request.
- Unlike HTTP flood attacks, rate limiting per IP does not help — the damage is done in
  one request.
- The circular schema is a normal design pattern; the vulnerability is the lack of depth limits.

### Vulnerable Configuration

```python
# VULNERABLE — no depth limit on query execution
app.add_url_rule(
    "/graphql",
    view_func=GraphQLView.as_view("graphql_view", schema=schema)
)
```

### Attack Script

See `attacks/graphql/depth_dos_attack.py` — sends a 15-level nested query and measures
response time to demonstrate server strain.

---

## 3. Alias / Batching Attack — "The Machine Gun"

### What It Is

GraphQL supports two features that attackers combine:

- **Aliases** — execute the same field multiple times in one query with different names.
- **Batching** — send multiple operations in one HTTP request body.

Together they allow an attacker to perform many actions while appearing to send just one HTTP
request.

### How the Attack Works

A normal brute-force login sends one password guess per HTTP request, making it detectable
by rate limiting (e.g. "max 5 login attempts per minute per IP").

An attacker bypasses this by packing 50 password guesses into one request using aliases:

```graphql
mutation BatchedLoginAttack {
  attempt1: login(username: "alice", password: "password1") { token }
  attempt2: login(username: "alice", password: "password2") { token }
  attempt3: login(username: "alice", password: "password3") { token }
  # ... up to attempt50
}
```

To the rate limiter, this is **one HTTP request**. Internally, the server runs 50 separate login
operations. If rate limiting is set to "5 requests per minute", the attacker can test 250
passwords per minute instead of 5.

### Why This Is Dangerous

- Completely bypasses IP-based and request-count-based rate limiting.
- Works against any expensive operation: login, password reset, OTP verification.
- The server processes every alias — there is no shortcut.
- Invisible in access logs unless the server logs operation count, not just request count.

### Vulnerable Configuration

```python
# VULNERABLE — no complexity or alias count limit
schema = strawberry.Schema(query=Query, mutation=Mutation)
```

### Attack Script

See `attacks/graphql/alias_batching_attack.py` — sends a single request containing 50 aliased
login mutations, prints which password succeeded.

---

## Vulnerability Summary

| Vulnerability | Root Cause | Impact |
|--------------|------------|--------|
| Introspection Abuse | Schema exposed in production | Reconnaissance, attack planning |
| Depth / Circular DoS | No query depth limit | Server CPU/memory exhaustion (DoS) |
| Alias / Batching | No query complexity budget | Rate limit bypass, credential stuffing |

---

## How GraphQL Vulnerabilities Differ from REST

| Dimension | REST | GraphQL |
|-----------|------|---------|
| Attack surface | Multiple endpoints | Single endpoint |
| Data enumeration | URL parameter manipulation | Introspection query |
| DoS vector | Flood of HTTP requests | Single deeply nested query |
| Rate limit bypass | Requires many requests | One request with many aliases |

---

## Next Steps

See [Security Mechanisms](04-security-mechanisms.md) for how each of these is mitigated.
