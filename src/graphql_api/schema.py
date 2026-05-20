from __future__ import annotations
import strawberry
from typing import List, Optional
from src.common.database import SessionLocal
from src.common.models import User, Post, Order
from src.common.auth import verify_password, generate_token


# ── GraphQL Types ────────────────────────────────────────────────────────────

@strawberry.type
class UserType:
    id: int
    username: str
    email: str
    bio: str

    @strawberry.field
    def posts(self) -> List[PostType]:
        """Circular relationship: User → posts → PostType.author → UserType
        This is the relationship exploited by the Depth/Circular DoS attack."""
        db = SessionLocal()
        try:
            db_posts = db.query(Post).filter(Post.author_id == self.id).all()
            return [
                PostType(id=p.id, title=p.title, content=p.content, author_id=p.author_id)
                for p in db_posts
            ]
        finally:
            db.close()


@strawberry.type
class PostType:
    id: int
    title: str
    content: str
    author_id: int

    @strawberry.field
    def author(self) -> Optional[UserType]:
        """Circular back-reference: Post → author → UserType.posts → PostType ...
        Together with UserType.posts this creates the never-ending loop."""
        db = SessionLocal()
        try:
            u = db.query(User).filter(User.id == self.author_id).first()
            if u:
                return UserType(id=u.id, username=u.username, email=u.email, bio=u.bio or "")
            return None
        finally:
            db.close()


@strawberry.type
class OrderType:
    id: int
    item_name: str
    amount: float


@strawberry.type
class AuthResponse:
    token: str
    user_id: int
    message: str


# ── Queries ──────────────────────────────────────────────────────────────────

@strawberry.type
class Query:
    @strawberry.field
    def user(self, id: int) -> Optional[UserType]:
        db = SessionLocal()
        try:
            u = db.query(User).filter(User.id == id).first()
            if u:
                return UserType(id=u.id, username=u.username, email=u.email, bio=u.bio or "")
            return None
        finally:
            db.close()

    @strawberry.field
    def users(self) -> List[UserType]:
        db = SessionLocal()
        try:
            all_users = db.query(User).all()
            return [
                UserType(id=u.id, username=u.username, email=u.email, bio=u.bio or "")
                for u in all_users
            ]
        finally:
            db.close()

    @strawberry.field
    def post(self, id: int) -> Optional[PostType]:
        db = SessionLocal()
        try:
            p = db.query(Post).filter(Post.id == id).first()
            if p:
                return PostType(id=p.id, title=p.title, content=p.content, author_id=p.author_id)
            return None
        finally:
            db.close()

    @strawberry.field
    def posts(self) -> List[PostType]:
        db = SessionLocal()
        try:
            all_posts = db.query(Post).all()
            return [
                PostType(id=p.id, title=p.title, content=p.content, author_id=p.author_id)
                for p in all_posts
            ]
        finally:
            db.close()


# ── Mutations ────────────────────────────────────────────────────────────────

@strawberry.type
class Mutation:
    @strawberry.mutation
    def login(self, username: str, password: str) -> AuthResponse:
        """Login mutation — target of the Alias/Batching attack.
        50 aliases of this mutation in one request bypasses rate limiting."""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == username).first()
            if user and verify_password(password, user.password_hash):
                token = generate_token(user.id, user.username)
                return AuthResponse(token=token, user_id=user.id, message="Login successful")
            return AuthResponse(token="", user_id=0, message="Invalid credentials")
        finally:
            db.close()

    @strawberry.mutation
    def register(self, username: str, email: str, password: str) -> AuthResponse:
        from src.common.auth import hash_password
        db = SessionLocal()
        try:
            existing = db.query(User).filter(User.username == username).first()
            if existing:
                return AuthResponse(token="", user_id=0, message="Username already taken")
            from src.common.models import User as UserModel
            new_user = UserModel(
                username=username,
                email=email,
                password_hash=hash_password(password),
                bio="",
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            token = generate_token(new_user.id, new_user.username)
            return AuthResponse(token=token, user_id=new_user.id, message="Registered")
        finally:
            db.close()


# ── Schema ───────────────────────────────────────────────────────────────────

schema = strawberry.Schema(query=Query, mutation=Mutation)
