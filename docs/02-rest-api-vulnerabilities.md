# REST API Vulnerabilities

REST APIs use predictable URLs, HTTP verbs, and JSON bodies. Their vulnerabilities typically
arise because the server trusts user-controlled identifiers and incoming data fields too easily.

This project demonstrates three REST API vulnerabilities: BOLA/IDOR, Mass Assignment, and
Excessive Data Exposure.

---

## 1. BOLA / IDOR — "The Number Guesser"

### What It Is

**BOLA** (Broken Object Level Authorization) is the same attack as **IDOR** (Insecure Direct
Object Reference). It is the #1 vulnerability on the OWASP API Security Top 10.

REST APIs commonly expose resources through predictable numeric IDs in the URL:

```
GET /api/orders/1001
GET /api/orders/1002
GET /api/orders/1003
```

Being authenticated is not the same as being authorised to read every record.

### How the Attack Works

1. Attacker logs in with a legitimate account.
2. Attacker observes the URL structure: `/api/orders/1001`.
3. Attacker increments the ID: `/api/orders/1002`, `/api/orders/1003`, ...
4. Server checks only that the user is logged in — it never checks *who owns* the order.
5. Server returns records belonging to other users.

The attacker can harvest records across the entire database simply by cycling through IDs.

### Vulnerable Code Pattern

```python
# VULNERABLE — only checks authentication, not ownership
@app.route("/api/orders/<int:order_id>")
@require_auth
def get_order(order_id):
    order = db.session.get(Order, order_id)   # finds ANY order by ID
    if not order:
        return {"error": "Not found"}, 404
    return order.to_dict(), 200               # no ownership check!
```

### Why This Is Dangerous

- No special tools required — a browser or `curl` is enough.
- Sequential integer IDs make enumeration trivial.
- Exposes PII, financial data, and any other per-user resource.

### Attack Script

See `attacks/rest/bola_attack.py` — cycles IDs 1–100, prints all unauthorised records returned.

---

## 2. Mass Assignment — "The Hidden Field Trick"

### What It Is

Mass Assignment occurs when the server automatically maps every field in the incoming JSON
request body directly to database columns — including fields the user interface never exposed.

Modern ORMs make this easy to do accidentally: a single line like `user.update(request.json)`
can silently set any database column.

### How the Attack Works

1. Attacker opens the profile-update form (only shows `name`, `email`, `bio`).
2. Attacker intercepts the outgoing request with browser DevTools or Burp Suite.
3. Attacker manually adds a hidden field: `"is_admin": true`.
4. Modified JSON is sent to `PUT /api/users/<id>`.
5. If the server forwards all fields to the ORM blindly, `is_admin` is saved to the database.
6. Attacker now has admin privileges.

### Vulnerable Code Pattern

```python
# VULNERABLE — copies every incoming field to the model
@app.route("/api/users/<int:user_id>", methods=["PUT"])
@require_auth
def update_user(user_id):
    data = request.json
    user = db.session.get(User, user_id)
    for key, value in data.items():         # iterates ALL fields
        setattr(user, key, value)           # sets even is_admin, password_hash, etc.
    db.session.commit()
    return {"message": "Updated"}, 200
```

### Why This Is Dangerous

- An attacker can escalate their own privileges to admin.
- Can overwrite `password_hash`, `email`, or internal system fields.
- The attack is invisible to the frontend; it happens entirely at the HTTP layer.

### Attack Script

See `attacks/rest/mass_assignment_attack.py` — sends `{"bio": "hello", "is_admin": true}` and
verifies the `is_admin` flag was stored.

---

## 3. Excessive Data Exposure — "The TMI Response"

### What It Is

The server returns the full database object to the client — including sensitive fields the UI
never displays. The frontend may hide these visually, but the raw JSON is fully readable in the
browser's Network tab.

### How the Attack Works

1. Attacker opens the profile page normally.
2. Attacker opens Browser DevTools → Network tab.
3. Attacker inspects the raw JSON response for `GET /api/users/profile`.
4. Response contains: `password_hash`, `is_admin`, `internal_notes`, `created_at`, `reset_token` — fields the UI never shows.
5. Attacker reads sensitive data directly from the response body.

No special privileges or tools required — just DevTools.

### Vulnerable Code Pattern

```python
# VULNERABLE — serialises the entire database row
@app.route("/api/users/profile")
@require_auth
def get_profile():
    user = db.session.get(User, current_user_id)
    return user.to_dict(), 200   # to_dict() exposes ALL columns
```

### Example Vulnerable Response

```json
{
  "id": 42,
  "username": "alice",
  "email": "alice@example.com",
  "password_hash": "$2b$12$...",
  "is_admin": false,
  "bio": "Hello world",
  "reset_token": "eyJ...",
  "created_at": "2024-01-15T10:30:00",
  "internal_notes": "Flagged for suspicious login from IP 1.2.3.4"
}
```

### Why This Is Dangerous

- Password hashes can be cracked offline.
- Password reset tokens allow account takeover.
- Internal notes may reveal security measures or investigations.
- `is_admin` flag reveals privilege level.

### Attack Script

See `attacks/rest/excessive_data_attack.py` — fetches the profile endpoint and logs all fields
present in the response that are not expected from the UI.

---

## Vulnerability Summary

| Vulnerability | Root Cause | OWASP API Top 10 |
|--------------|------------|-----------------|
| BOLA / IDOR | Missing ownership check | API1:2023 |
| Mass Assignment | Blind trust of all input fields | API3:2023 |
| Excessive Data Exposure | No output filtering / public schema | API3:2023 |

---

## Next Steps

See [Security Mechanisms](04-security-mechanisms.md) for how each of these is mitigated.
