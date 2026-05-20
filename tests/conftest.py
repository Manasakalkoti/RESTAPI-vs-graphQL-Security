import os
import pytest

# Set test DB and secret BEFORE any app import
os.environ["DATABASE_URL"] = "sqlite:///test_lab.db"
os.environ["JWT_SECRET"] = "test-secret-key"
os.environ["DISABLE_INTROSPECTION"] = "false"

from src.common.database import init_db, engine, Base, SessionLocal
from src.common.models import User, Post, Order
from src.common.auth import hash_password, generate_token
from src.rest_api.app import create_app as create_rest_app
from src.graphql_api.app import create_app as create_gql_app


# ── Database setup ───────────────────────────────────────────────────────────

def _seed_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    alice = User(username="alice", email="alice@test.com",
                 password_hash=hash_password("password123"),
                 bio="Alice bio", is_admin=False,
                 reset_token="tok_reset_alice", internal_notes="Alice internal note")
    bob   = User(username="bob",   email="bob@test.com",
                 password_hash=hash_password("password123"),
                 bio="Bob bio",   is_admin=False,
                 reset_token=None, internal_notes="Bob internal note")
    db.add_all([alice, bob])
    db.flush()

    db.add_all([
        Post(title="Alice Post 1", content="Content 1", author_id=alice.id),
        Post(title="Bob Post 1",   content="Content 2", author_id=bob.id),
    ])

    # Alice owns orders 1-3, Bob owns 4-5
    db.add_all([
        Order(item_name="Laptop",    amount=1200.0, user_id=alice.id, internal_notes="Alice note"),
        Order(item_name="Mouse",     amount=29.99,  user_id=alice.id, internal_notes=None),
        Order(item_name="Keyboard",  amount=79.99,  user_id=alice.id, internal_notes=None),
        Order(item_name="Desk Chair",amount=450.0,  user_id=bob.id,   internal_notes="Bob note"),
        Order(item_name="Headphones",amount=199.99, user_id=bob.id,   internal_notes=None),
    ])
    db.commit()

    alice_id = alice.id
    bob_id   = bob.id
    db.close()
    return alice_id, bob_id


@pytest.fixture(scope="session")
def db_ids():
    return _seed_test_db()


# ── REST app fixtures ─────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def vuln_rest(db_ids):
    app = create_rest_app(secure=False)
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture(scope="session")
def sec_rest(db_ids):
    app = create_rest_app(secure=True)
    app.config["TESTING"] = True
    return app.test_client()


# ── GraphQL app fixtures ──────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def vuln_gql(db_ids):
    os.environ["DISABLE_INTROSPECTION"] = "false"
    app = create_gql_app(secure=False)
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture(scope="session")
def sec_gql(db_ids):
    os.environ["DISABLE_INTROSPECTION"] = "true"
    app = create_gql_app(secure=True)
    app.config["TESTING"] = True
    return app.test_client()


# ── Auth token fixtures ───────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def alice_token(db_ids):
    alice_id, _ = db_ids
    return generate_token(alice_id, "alice")


@pytest.fixture(scope="session")
def bob_token(db_ids):
    _, bob_id = db_ids
    return generate_token(bob_id, "bob")
