"""
REST API — Vulnerability Confirmation Tests
Prove that all three attacks SUCCEED on the VULNERABLE server (SECURE_MODE=false).
"""
import json
import pytest


class TestBOLAVulnerable:
    def test_alice_can_read_bobs_order(self, vuln_rest, alice_token, db_ids):
        """Alice (user 1) must NOT read Bob's order — but on vulnerable API she can."""
        _, bob_id = db_ids
        headers = {"Authorization": f"Bearer {alice_token}"}

        # Bob's orders start at ID 4 in seeded test data
        for order_id in range(4, 6):
            r = vuln_rest.get(f"/api/orders/{order_id}", headers=headers)
            assert r.status_code == 200, (
                f"Expected 200 (attack succeeds) for order {order_id}, got {r.status_code}"
            )
            data = r.get_json()
            # Confirm it's bob's order
            assert data.get("user_id") == bob_id or "item_name" in data

    def test_returns_sensitive_order_fields(self, vuln_rest, alice_token):
        headers = {"Authorization": f"Bearer {alice_token}"}
        r = vuln_rest.get("/api/orders/1", headers=headers)
        assert r.status_code == 200
        data = r.get_json()
        # Vulnerable mode exposes internal_notes
        assert "internal_notes" in data


class TestMassAssignmentVulnerable:
    def test_injecting_is_admin_succeeds(self, vuln_rest, alice_token, db_ids):
        """On vulnerable API, is_admin=True in PUT body should be stored."""
        alice_id, _ = db_ids
        headers = {"Authorization": f"Bearer {alice_token}"}

        # Check before
        r = vuln_rest.get(f"/api/users/{alice_id}", headers=headers)
        assert r.get_json()["is_admin"] is False

        # Inject is_admin
        vuln_rest.put(
            f"/api/users/{alice_id}",
            json={"bio": "hacked", "is_admin": True},
            headers=headers,
        )

        # Verify flag was stored
        r2 = vuln_rest.get(f"/api/users/{alice_id}", headers=headers)
        assert r2.get_json()["is_admin"] is True, "Mass assignment should have escalated is_admin"

        # Cleanup
        vuln_rest.put(f"/api/users/{alice_id}", json={"is_admin": False}, headers=headers)

    def test_extra_fields_are_written(self, vuln_rest, alice_token, db_ids):
        alice_id, _ = db_ids
        headers = {"Authorization": f"Bearer {alice_token}"}
        r = vuln_rest.put(
            f"/api/users/{alice_id}",
            json={"bio": "test bio"},
            headers=headers,
        )
        assert r.status_code == 200


class TestExcessiveDataExposureVulnerable:
    def test_profile_exposes_password_hash(self, vuln_rest, alice_token):
        headers = {"Authorization": f"Bearer {alice_token}"}
        r = vuln_rest.get("/api/users/profile", headers=headers)
        assert r.status_code == 200
        data = r.get_json()
        assert "password_hash" in data, "Vulnerable API must expose password_hash"

    def test_profile_exposes_reset_token(self, vuln_rest, alice_token):
        headers = {"Authorization": f"Bearer {alice_token}"}
        r = vuln_rest.get("/api/users/profile", headers=headers)
        data = r.get_json()
        assert "reset_token" in data, "Vulnerable API must expose reset_token"

    def test_profile_exposes_internal_notes(self, vuln_rest, alice_token):
        headers = {"Authorization": f"Bearer {alice_token}"}
        r = vuln_rest.get("/api/users/profile", headers=headers)
        data = r.get_json()
        assert "internal_notes" in data, "Vulnerable API must expose internal_notes"

    def test_profile_exposes_is_admin(self, vuln_rest, alice_token):
        headers = {"Authorization": f"Bearer {alice_token}"}
        r = vuln_rest.get("/api/users/profile", headers=headers)
        data = r.get_json()
        assert "is_admin" in data, "Vulnerable API must expose is_admin"
