# Attack Comparison — REST vs GraphQL

This document provides a side-by-side analysis of the attack surfaces, attack vectors, and
defensive strategies for REST APIs and GraphQL APIs.

---

## Structural Differences That Drive Different Attacks

| Dimension | REST | GraphQL |
|-----------|------|---------|
| Endpoint count | Many (one per resource) | One (`/graphql`) |
| Request structure | URL + HTTP verb + JSON body | Query / Mutation string in JSON |
| Data selection | Server-defined (fixed response shape) | Client-defined (client picks fields) |
| Schema discovery | No built-in mechanism | Built-in introspection |
| Query nesting | Not supported (flat resources) | Unlimited by default |
| Request batching | One operation per request | Multiple operations in one request |

These structural differences mean REST and GraphQL are vulnerable to fundamentally different
attack classes — not just different versions of the same attack.

---

## Attack-by-Attack Comparison

### Reconnaissance (Learning the API)

| Aspect | REST | GraphQL |
|--------|------|---------|
| How attackers discover endpoints | Brute-force URL guessing, JS bundle analysis | Single `__schema` introspection query |
| Effort required | High — must guess or find endpoint names | None — server hands over the full map |
| Information gained | Endpoint names and URL patterns | Full type system, all fields, all relationships |
| Mitigation | Security through obscurity (partial), API gateway | Disable introspection in production |

**Key insight:** GraphQL introspection is dramatically more powerful than REST enumeration.
One query returns everything; REST enumeration may never find hidden endpoints.

---

### Denial of Service (Exhausting the Server)

| Aspect | REST | GraphQL |
|--------|------|---------|
| DoS via a single request | Difficult — each request is bounded | Easy — one deeply nested query |
| Circular relationships | Not possible in REST data model | Normal schema feature, exploitable |
| Processing cost per request | Predictable (fixed endpoint logic) | Unpredictable (client-chosen depth) |
| Mitigation | Standard rate limiting works | Rate limiting insufficient; need depth limits |

**Key insight:** GraphQL's circular query DoS requires only one request to bring down the
server. REST DoS typically requires many requests, making it easier to detect and block.

---

### Rate Limit Bypass

| Aspect | REST | GraphQL |
|--------|------|---------|
| Unit of measurement | HTTP request | HTTP request |
| Operations per request | 1 | Unlimited (via aliases/batching) |
| Brute-force login attempts per "request" | 1 | 50–500+ |
| Standard rate limiting effectiveness | Effective | Completely bypassed |
| Required mitigation | Request rate limiting | Complexity budget (measures operations, not requests) |

**Key insight:** Rate limiting is the standard defence against brute-force in REST. In GraphQL,
rate limiting is meaningless without a complexity budget because a single request can contain
hundreds of operations.

---

### Broken Access Control (Accessing Other Users' Data)

| Aspect | REST | GraphQL |
|--------|------|---------|
| Attack method | Change numeric ID in URL | Query for another user's related data |
| Visibility | Explicit in URL | Embedded in nested query |
| Mitigation | Ownership check in route handler | Field-level authorization in resolvers |
| Difficulty to detect | Easy to spot in access logs | Harder — single endpoint, complex query body |

---

### Data Over-Exposure

| Aspect | REST | GraphQL |
|--------|------|---------|
| Root cause | Server returns full DB object | Client requests all fields explicitly |
| Direction | Server pushes too much | Client pulls too much (by design) |
| Mitigation | Marshmallow public schema | Field-level authorization + schema design |
| GraphQL advantage | N/A | Clients request only what they need — less over-exposure by default |

**Key insight:** GraphQL is architecturally better at avoiding data over-exposure because
clients must explicitly request each field. REST returns everything in the response regardless
of what the UI needs.

---

## Attack Surface Visualisation

```
REST Attack Surface:
┌─────────────────────────────────────────────────────────┐
│  GET  /api/users/:id          ← BOLA target             │
│  PUT  /api/users/:id          ← Mass Assignment target  │
│  GET  /api/users/profile      ← Data Exposure target    │
│  GET  /api/orders/:id         ← BOLA target             │
│  POST /api/auth/login         ← Brute-force target      │
│  ...many more endpoints...                              │
└─────────────────────────────────────────────────────────┘

GraphQL Attack Surface:
┌─────────────────────────────────────────────────────────┐
│  POST /graphql                                          │
│    ├─ __schema query          ← Introspection target    │
│    ├─ Deep nested query       ← Depth DoS target        │
│    └─ Aliased mutations       ← Batching target         │
└─────────────────────────────────────────────────────────┘
```

---

## Which API Is More Secure "Out of the Box"?

Neither — they have different security profiles:

| Security Property | REST Default | GraphQL Default |
|-----------------|--------------|----------------|
| Schema hidden from attackers | Yes (no introspection) | No (introspection on) |
| DoS resistance | Higher (bounded responses) | Lower (unbounded nesting) |
| Rate limit effectiveness | High | Low without complexity limits |
| Data minimisation | Poor (fixed over-returns) | Good (client requests only what's needed) |
| Access control granularity | Endpoint-level | Field-level (more precise) |

REST is harder to map but easier to exploit once the structure is known.
GraphQL is easier to map but offers more fine-grained access control once properly configured.

---

## Mitigation Comparison

| Vulnerability | REST Mitigation | GraphQL Mitigation |
|--------------|----------------|-------------------|
| Reconnaissance | N/A (no built-in schema) | Disable introspection in production |
| DoS | HTTP rate limiting | Query depth limit |
| Rate limit bypass | IP-based rate limiting | Query complexity budget |
| Broken access control | Ownership check per endpoint | Resolver-level authorization |
| Data over-exposure | Marshmallow public schema | Schema type design + field resolvers |
