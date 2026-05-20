from src.common.database import SessionLocal, init_db
from src.common.models import User, Post, Order
from src.common.auth import hash_password


USERS = [
    {"username": "alice",   "email": "alice@example.com",   "password": "password123", "bio": "Alice's bio",   "is_admin": False, "internal_notes": "Flagged for 3 failed logins on 2024-01-10", "reset_token": "tok_alice_reset_abc123"},
    {"username": "bob",     "email": "bob@example.com",     "password": "password123", "bio": "Bob's bio",     "is_admin": False, "internal_notes": "VIP customer, high spend account",          "reset_token": None},
    {"username": "charlie", "email": "charlie@example.com", "password": "password123", "bio": "Charlie's bio", "is_admin": True,  "internal_notes": "Admin account, do not expose",              "reset_token": None},
]

POSTS = [
    {"title": "Alice Post 1",   "content": "Content from Alice 1",   "author_username": "alice"},
    {"title": "Alice Post 2",   "content": "Content from Alice 2",   "author_username": "alice"},
    {"title": "Alice Post 3",   "content": "Content from Alice 3",   "author_username": "alice"},
    {"title": "Bob Post 1",     "content": "Content from Bob 1",     "author_username": "bob"},
    {"title": "Bob Post 2",     "content": "Content from Bob 2",     "author_username": "bob"},
    {"title": "Charlie Post 1", "content": "Content from Charlie 1", "author_username": "charlie"},
]

ORDERS = [
    # Alice owns orders 1-5
    {"item_name": "Laptop",       "amount": 1200.00, "owner_username": "alice",   "internal_notes": "Order placed via mobile app"},
    {"item_name": "Mouse",        "amount": 29.99,   "owner_username": "alice",   "internal_notes": "Discount applied"},
    {"item_name": "Keyboard",     "amount": 79.99,   "owner_username": "alice",   "internal_notes": None},
    {"item_name": "Monitor",      "amount": 349.00,  "owner_username": "alice",   "internal_notes": "Awaiting delivery"},
    {"item_name": "Webcam",       "amount": 59.99,   "owner_username": "alice",   "internal_notes": None},
    # Bob owns orders 6-10
    {"item_name": "Desk Chair",   "amount": 450.00,  "owner_username": "bob",     "internal_notes": "Corporate account purchase"},
    {"item_name": "Headphones",   "amount": 199.99,  "owner_username": "bob",     "internal_notes": None},
    {"item_name": "USB Hub",      "amount": 39.99,   "owner_username": "bob",     "internal_notes": None},
    {"item_name": "Desk Lamp",    "amount": 49.99,   "owner_username": "bob",     "internal_notes": "Gift order"},
    {"item_name": "Cable Pack",   "amount": 19.99,   "owner_username": "bob",     "internal_notes": None},
    # Charlie owns orders 11-12
    {"item_name": "Server Rack",  "amount": 3500.00, "owner_username": "charlie", "internal_notes": "Admin purchase, no VAT"},
    {"item_name": "UPS Battery",  "amount": 299.00,  "owner_username": "charlie", "internal_notes": None},
]


def seed():
    init_db()
    db = SessionLocal()

    if db.query(User).count() > 0:
        print("[Seed] Database already seeded. Skipping.")
        db.close()
        return

    user_map = {}
    for u in USERS:
        user = User(
            username=u["username"],
            email=u["email"],
            password_hash=hash_password(u["password"]),
            bio=u["bio"],
            is_admin=u["is_admin"],
            internal_notes=u["internal_notes"],
            reset_token=u["reset_token"],
        )
        db.add(user)
        db.flush()
        user_map[u["username"]] = user

    for p in POSTS:
        post = Post(
            title=p["title"],
            content=p["content"],
            author_id=user_map[p["author_username"]].id,
        )
        db.add(post)

    for o in ORDERS:
        order = Order(
            item_name=o["item_name"],
            amount=o["amount"],
            user_id=user_map[o["owner_username"]].id,
            internal_notes=o["internal_notes"],
        )
        db.add(order)

    db.commit()
    db.close()
    print("[Seed] Database seeded: 3 users, 6 posts, 12 orders.")


if __name__ == "__main__":
    seed()
