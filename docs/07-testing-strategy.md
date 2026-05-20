# Testing Strategy

The test suite serves two purposes:
1. **Prove exploitability** — confirm that the vulnerable APIs are actually exploitable.
2. **Prove security** — confirm that the hardened APIs block every attack.

Both sets of tests are essential. Without the first set, there is no guarantee the
vulnerabilities are real. Without the second set, there is no guarantee the defences work.

---

## Test Architecture

```
tests/
├── conftest.py                         # Shared fixtures
├── test_rest_vulnerabilities.py        # REST attacks succeed on vulnerable API
├── test_rest_security.py               # REST attacks fail on secured API
├── test_graphql_vulnerabilities.py     # GraphQL attacks succeed on vulnerable API
└── test_graphql_security.py            # GraphQL attacks fail on secured API
```

---

## Fixtures (`tests/conftest.py`)

```python
import pytest
from src.rest_api.app import create_app as create_rest_app
from src.graphql_api.app import create_app as create_graphql_app
from src.common.database import Base, engine
from src.common.seed import seed_test_data

@pytest.fixture(scope="session")
def vulnerable_rest_client():
    app = create_rest_app(secure=False)
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(scope="session")
def secured_rest_client():
    app = create_rest_app(secure=True)
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(scope="session")
def auth_token_user_alice(vulnerable_rest_client):
    """JWT for user 'alice' (owns orders 1–5)."""
    resp = vulnerable_rest_client.post("/api/auth/login", json={
        "username": "alice", "password": "password123"
    })
    return resp.json["token"]

@pytest.fixture(scope="session")
def auth_token_user_bob(vulnerable_rest_client):
    """JWT for user 'bob' (owns orders 6–10)."""
    resp = vulnerable_rest_client.post("/api/auth/login", json={
        "username": "bob", "password": "password123"
    })
    return resp.json["token"]
```

---

## REST Vulnerability Tests

### `test_rest_vulnerabilities.py`

#### BOLA / IDOR

```python
def test_bola_vulnerable_alice_can_read_bobs_order(
    vulnerable_rest_client, auth_token_user_alice
):
    """Alice (user 1) should NOT access Bob's order (id=6) — but on vulnerable API, she can."""
    resp = vulnerable_rest_client.get(
        "/api/orders/6",
        headers={"Authorization": f"Bearer {auth_token_user_alice}"}
    )
    assert resp.status_code == 200                      # vulnerable: returns Bob's order
    assert resp.json["user_id"] != 1                    # confirms it's not Alice's data
```

#### Mass Assignment

```python
def test_mass_assignment_vulnerable_user_can_set_is_admin(
    vulnerable_rest_client, auth_token_user_alice
):
    """On vulnerable API, including is_admin in PUT body should escalate privileges."""
    resp = vulnerable_rest_client.put(
        "/api/users/1",
        json={"bio": "hacker", "is_admin": True},
        headers={"Authorization": f"Bearer {auth_token_user_alice}"}
    )
    assert resp.status_code == 200
    # Verify the flag was actually stored
    profile = vulnerable_rest_client.get(
        "/api/users/1",
        headers={"Authorization": f"Bearer {auth_token_user_alice}"}
    )
    assert profile.json["is_admin"] is True             # vulnerable: privilege escalated
```

#### Excessive Data Exposure

```python
def test_excessive_data_vulnerable_response_contains_password_hash(
    vulnerable_rest_client, auth_token_user_alice
):
    resp = vulnerable_rest_client.get(
        "/api/users/profile",
        headers={"Authorization": f"Bearer {auth_token_user_alice}"}
    )
    assert resp.status_code == 200
    assert "password_hash" in resp.json                 # vulnerable: sensitive field exposed
    assert "reset_token" in resp.json                   # vulnerable: token exposed
```

---

## REST Security Tests

### `test_rest_security.py`

#### BOLA Protection

```python
def test_bola_secured_alice_cannot_read_bobs_order(
    secured_rest_client, auth_token_user_alice
):
    resp = secured_rest_client.get(
        "/api/orders/6",
        headers={"Authorization": f"Bearer {auth_token_user_alice}"}
    )
    assert resp.status_code == 404                      # secured: not found (ownership mismatch)
```

#### Mass Assignment Protection

```python
def test_mass_assignment_secured_is_admin_is_ignored(
    secured_rest_client, auth_token_user_alice
):
    secured_rest_client.put(
        "/api/users/1",
        json={"bio": "hacker", "is_admin": True},
        headers={"Authorization": f"Bearer {auth_token_user_alice}"}
    )
    profile = secured_rest_client.get(
        "/api/users/profile",
        headers={"Authorization": f"Bearer {auth_token_user_alice}"}
    )
    assert profile.json.get("is_admin") is not True     # secured: flag not changed
```

#### Excessive Data Exposure Protection

```python
def test_data_exposure_secured_response_hides_sensitive_fields(
    secured_rest_client, auth_token_user_alice
):
    resp = secured_rest_client.get(
        "/api/users/profile",
        headers={"Authorization": f"Bearer {auth_token_user_alice}"}
    )
    assert resp.status_code == 200
    assert "password_hash" not in resp.json             # secured: field hidden
    assert "reset_token" not in resp.json               # secured: field hidden
    assert "is_admin" not in resp.json                  # secured: field hidden
    assert "username" in resp.json                      # normal fields still present
```

---

## GraphQL Tests

### `test_graphql_vulnerabilities.py`

#### Introspection Abuse

```python
def test_introspection_vulnerable_returns_schema(vulnerable_graphql_client):
    resp = vulnerable_graphql_client.post("/graphql", json={
        "query": "{ __schema { types { name } } }"
    })
    assert resp.status_code == 200
    types = resp.json["data"]["__schema"]["types"]
    assert len(types) > 0                               # vulnerable: schema returned
```

#### Depth DoS

```python
def test_depth_dos_vulnerable_deep_query_accepted(vulnerable_graphql_client):
    deep_query = """
    { user(id: 1) { posts { author { posts { author { posts { author { username } } } } } } } }
    """
    resp = vulnerable_graphql_client.post("/graphql", json={"query": deep_query})
    assert resp.status_code == 200                      # vulnerable: deep query accepted
```

### `test_graphql_security.py`

#### Introspection Protection

```python
def test_introspection_secured_schema_blocked(secured_graphql_client):
    resp = secured_graphql_client.post("/graphql", json={
        "query": "{ __schema { types { name } } }"
    })
    assert resp.status_code in (400, 200)
    if resp.status_code == 200:
        assert resp.json.get("errors") is not None      # secured: error returned

def test_introspection_secured_normal_query_still_works(secured_graphql_client):
    resp = secured_graphql_client.post("/graphql", json={
        "query": "{ user(id: 1) { username } }"
    })
    assert resp.status_code == 200
    assert "errors" not in resp.json                    # secured: normal query unaffected
```

#### Depth Limit

```python
def test_depth_limit_secured_deep_query_rejected(secured_graphql_client):
    deep_query = """
    { user(id:1) { posts { author { posts { author { posts { author { username } } } } } } } }
    """
    resp = secured_graphql_client.post("/graphql", json={"query": deep_query})
    assert resp.status_code == 400                      # secured: depth > 5 rejected
```

#### Complexity Budget

```python
def test_complexity_secured_batched_login_rejected(secured_graphql_client):
    aliases = "\n".join(
        f'attempt{i}: login(username:"alice", password:"pass{i}") {{ token }}'
        for i in range(1, 51)
    )
    resp = secured_graphql_client.post("/graphql", json={
        "query": f"mutation {{ {aliases} }}"
    })
    assert resp.status_code == 400                      # secured: complexity > 100 rejected
```

---

## Coverage Target

| Module | Target |
|--------|--------|
| `src/rest_api/` | >= 85% |
| `src/graphql_api/` | >= 80% |
| `src/common/` | >= 90% |
| `attacks/` | Not measured (scripts, not library code) |
| **Overall** | **>= 80%** |

### Running Coverage

```bash
pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html
# HTML report: htmlcov/index.html
```

---

## CI Integration

Add to `.github/workflows/test.yml`:

```yaml
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest tests/ -v --cov=src --cov-fail-under=80
```
