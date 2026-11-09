
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/auth", tags=["Authentication"])

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "database" / "users.sqlite"

hasher = PasswordHasher()
bearer = HTTPBearer()


def get_secret():
    secret = os.getenv("AUTH_SECRET_KEY")
    if not secret or len(secret) < 32:
        raise RuntimeError(
            "AUTH_SECRET_KEY must contain at least 32 characters."
        )
    return secret


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def normalize_email(email):
    return str(email).strip().lower()


def create_token(user_id):
    now = datetime.now(timezone.utc)

    return jwt.encode(
        {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(hours=1),
        },
        get_secret(),
        algorithm="HS256",
    )


@router.post("/register", status_code=201)
def register(request: RegisterRequest):
    init_db()

    email = normalize_email(request.email)
    password_hash = hasher.hash(request.password)

    try:
        with get_db() as db:
            cursor = db.execute(
                """
                INSERT INTO users
                    (email, password_hash, created_at)
                VALUES (?, ?, ?)
                """,
                (
                    email,
                    password_hash,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            user_id = cursor.lastrowid

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="This email is already registered.",
        )

    return {
        "id": user_id,
        "email": email,
        "message": "Account created successfully.",
    }


@router.post("/login")
def login(request: LoginRequest):
    init_db()

    email = normalize_email(request.email)

    with get_db() as db:
        user = db.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,),
        ).fetchone()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    try:
        hasher.verify(user["password_hash"], request.password)
    except (VerifyMismatchError, VerificationError):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    return {
        "access_token": create_token(user["id"]),
        "token_type": "bearer",
        "email": user["email"],
    }


def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
):
    try:
        payload = jwt.decode(
            credentials.credentials,
            get_secret(),
            algorithms=["HS256"],
        )
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        )

    with get_db() as db:
        user = db.execute(
            "SELECT id, email FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found.",
        )

    return dict(user)


@router.get("/me")
def get_me(user=Depends(current_user)):
    return user
