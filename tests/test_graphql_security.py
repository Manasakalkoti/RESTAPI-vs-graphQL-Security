"""
GraphQL API — Security Mechanism Tests
Prove that all three attacks are BLOCKED on the SECURED server (SECURE_MODE=true).
Also verify that normal queries still work after hardening.
"""
import pytest


GQL = "/graphql"

INTROSPECTION_QUERY = '{ __schema { types { name } } }'

SAFE_QUERY   = '{ user(id: 1) { username email } }'

DEEP_QUERY = """
{
  user(id: 1) {
    username
    posts {
      title
      author {
        username
        posts {
          title
          author {
            username
            posts { title author { username } }
          }
        }
      }
    }
  }
}
"""

SHALLOW_QUERY = '{ user(id: 1) { username posts { title } } }'


def batched_login(n=50):
    aliases = "\n  ".join(
        f'a{i}: login(username: "alice", password: "wrongpass{i}") {{ token message }}'
        for i in range(1, n + 1)
    )
    return f"mutation {{ {aliases} }}"


class TestIntrospectionSecured:
    def test_schema_query_is_blocked(self, sec_gql):
        r = sec_gql.post(GQL, json={"query": INTROSPECTION_QUERY},
                         content_type="application/json")
        assert r.status_code == 400, (
            f"Secured server must block introspection with 400, got {r.status_code}"
        )

    def test_error_message_is_clear(self, sec_gql):
        r = sec_gql.post(GQL, json={"query": INTROSPECTION_QUERY},
                         content_type="application/json")
        data = r.get_json()
        msg = data.get("errors", [{}])[0].get("message", "").lower()
        assert "introspection" in msg or "disabled" in msg, (
            f"Error message must mention introspection, got: {msg}"
        )

    def test_normal_query_still_works(self, sec_gql):
        """Introspection block must not affect legitimate queries."""
        r = sec_gql.post(GQL, json={"query": SAFE_QUERY},
                         content_type="application/json")
        assert r.status_code == 200
        data = r.get_json()
        assert "errors" not in data
        assert data["data"]["user"]["username"] == "alice"


class TestDepthLimitSecured:
    def test_deep_query_is_rejected(self, sec_gql):
        r = sec_gql.post(GQL, json={"query": DEEP_QUERY},
                         content_type="application/json")
        assert r.status_code == 400, (
            f"Secured server must reject deep query with 400, got {r.status_code}"
        )

    def test_depth_error_message(self, sec_gql):
        r = sec_gql.post(GQL, json={"query": DEEP_QUERY},
                         content_type="application/json")
        data = r.get_json()
        msg = data.get("errors", [{}])[0].get("message", "").lower()
        assert "depth" in msg, f"Error must mention depth, got: {msg}"

    def test_shallow_query_passes(self, sec_gql):
        """Queries within depth limit must still work."""
        r = sec_gql.post(GQL, json={"query": SHALLOW_QUERY},
                         content_type="application/json")
        assert r.status_code == 200
        data = r.get_json()
        assert "errors" not in data
        assert data["data"]["user"] is not None


class TestComplexityBudgetSecured:
    def test_batched_login_is_rejected(self, sec_gql):
        r = sec_gql.post(GQL, json={"query": batched_login(50)},
                         content_type="application/json")
        assert r.status_code == 400, (
            f"Secured server must reject 50-alias batch with 400, got {r.status_code}"
        )

    def test_complexity_error_message(self, sec_gql):
        r = sec_gql.post(GQL, json={"query": batched_login(50)},
                         content_type="application/json")
        data = r.get_json()
        msg = data.get("errors", [{}])[0].get("message", "").lower()
        assert "complexity" in msg or "budget" in msg, (
            f"Error must mention complexity, got: {msg}"
        )

    def test_single_login_passes(self, sec_gql):
        """A single legitimate login mutation must still work."""
        query = 'mutation { login(username: "alice", password: "password123") { token message } }'
        r = sec_gql.post(GQL, json={"query": query},
                         content_type="application/json")
        assert r.status_code == 200
        data = r.get_json()
        assert "errors" not in data
        assert data["data"]["login"]["token"] != ""
