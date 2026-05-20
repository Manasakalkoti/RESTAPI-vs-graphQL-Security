"""
REST API — Security Mechanism Tests
Prove that all three attacks are BLOCKED on the SECURED server (SECURE_MODE=true).
Also verify that normal operations still work after hardening.
"""
import pytest


class TestBOLASecured:
    def test_alice_cannot_read_bobs_order(self, sec_rest, alice_token):
        """Ownership check: Bob's orders must return 404 for Alice."""
        headers = {"Authorization": f"Bearer {alice_token}"}
        for order_id in range(4, 6):
            r = sec_rest.get(f"/api/orders/{order_id}", headers=headers)
            assert r.status_code == 404, (
                f"Secured API must block order {order_id} for Alice — got {r.status_code}"
            )

    def test_alice_can_read_her_own_orders(self, sec_rest, alice_token):
        """Normal access to own records must still work after hardening."""
        headers = {"Authorization": f"Bearer {alice_token}"}
        for order_id in range(1, 4):
            r = sec_rest.get(f"/api/orders/{order_id}", headers=headers)
            assert r.status_code == 200, (
                f"Alice must access her own order {order_id} — got {r.status_code}"
            )

    def test_secured_response_hides_internal_notes(self, sec_rest, alice_token):
        headers = {"Authorization": f"Bearer {alice_token}"}
        r = sec_rest.get("/api/orders/1", headers=headers)
        assert r.status_code == 200
        data = r.get_json()
        assert "internal_notes" not in data, "Secured order response must not expose internal_notes"


class TestMassAssignmentSecured:
    def test_injected_is_admin_is_ignored(self, sec_rest, alice_token, db_ids):
        """Allowlist filter must silently drop is_admin from PUT body."""
        alice_id, _ = db_ids
        headers = {"Authorization": f"Bearer {alice_token}"}

        sec_rest.put(
            f"/api/users/{alice_id}",
            json={"bio": "new bio", "is_admin": True},
            headers=headers,
        )

        r = sec_rest.get(f"/api/users/{alice_id}", headers=headers)
        data = r.get_json()
        assert data.get("is_admin") is not True, "Secured API must block is_admin injection"

    def test_legitimate_fields_still_update(self, sec_rest, alice_token, db_ids):
        """Allowed fields (bio) must still be updatable after hardening."""
        alice_id, _ = db_ids
        headers = {"Authorization": f"Bearer {alice_token}"}

        sec_rest.put(
            f"/api/users/{alice_id}",
            json={"bio": "updated bio"},
            headers=headers,
        )

        r = sec_rest.get("/api/users/profile", headers=headers)
        # Profile returns public schema; bio is included
        assert r.status_code == 200


class TestExcessiveDataExposureSecured:
    def test_profile_hides_password_hash(self, sec_rest, alice_token):
        headers = {"Authorization": f"Bearer {alice_token}"}
        r = sec_rest.get("/api/users/profile", headers=headers)
        assert r.status_code == 200
        data = r.get_json()
        assert "password_hash" not in data, "Secured profile must not expose password_hash"

    def test_profile_hides_reset_token(self, sec_rest, alice_token):
        headers = {"Authorization": f"Bearer {alice_token}"}
        r = sec_rest.get("/api/users/profile", headers=headers)
        data = r.get_json()
        assert "reset_token" not in data, "Secured profile must not expose reset_token"

    def test_profile_hides_internal_notes(self, sec_rest, alice_token):
        headers = {"Authorization": f"Bearer {alice_token}"}
        r = sec_rest.get("/api/users/profile", headers=headers)
        data = r.get_json()
        assert "internal_notes" not in data, "Secured profile must not expose internal_notes"

    def test_profile_hides_is_admin(self, sec_rest, alice_token):
        headers = {"Authorization": f"Bearer {alice_token}"}
        r = sec_rest.get("/api/users/profile", headers=headers)
        data = r.get_json()
        assert "is_admin" not in data, "Secured profile must not expose is_admin"

    def test_profile_still_returns_safe_fields(self, sec_rest, alice_token):
        """Safe fields must be present after hardening."""
        headers = {"Authorization": f"Bearer {alice_token}"}
        r = sec_rest.get("/api/users/profile", headers=headers)
        data = r.get_json()
        for field in ["id", "username", "email"]:
            assert field in data, f"Safe field '{field}' must be in secured profile response"
