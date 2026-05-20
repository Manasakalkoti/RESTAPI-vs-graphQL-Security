from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from src.common.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)   # sensitive — excluded from public schema
    is_admin = Column(Boolean, default=False)              # sensitive — mass assignment target
    bio = Column(String(500), default="")
    reset_token = Column(String(256), nullable=True)       # sensitive — excluded from public schema
    internal_notes = Column(Text, nullable=True)           # sensitive — excluded from public schema

    posts = relationship("Post", back_populates="author", lazy="select")
    orders = relationship("Order", back_populates="user", lazy="select")

    def to_dict(self):
        """Full dict — intentionally exposes sensitive fields (used in VULNERABLE mode)."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "is_admin": self.is_admin,
            "bio": self.bio,
            "reset_token": self.reset_token,
            "internal_notes": self.internal_notes,
        }


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Circular relationship: Post → author (User) → posts (Post[]) — depth DoS enabler
    author = relationship("User", back_populates="posts", lazy="select")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # ownership field — BOLA target
    item_name = Column(String(200), nullable=False)
    amount = Column(Float, nullable=False)
    internal_notes = Column(Text, nullable=True)   # sensitive — excluded from public schema

    user = relationship("User", back_populates="orders", lazy="select")

    def to_dict(self):
        """Full dict — intentionally exposes sensitive fields (used in VULNERABLE mode)."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "item_name": self.item_name,
            "amount": self.amount,
            "internal_notes": self.internal_notes,
        }
