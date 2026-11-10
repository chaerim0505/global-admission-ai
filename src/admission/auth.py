
import os
import sqlite3
from contextlib import contextmanager
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


# ---------------------------------------------------------------
# Database
# DATABASE_URL이 있으면 Postgres(Neon 등)에 영구 저장하고,
# 없으면 로컬 개발용 SQLite 파일을 사용한다.
# ---------------------------------------------------------------

def database_url():
    return (os.getenv("DATABASE_URL") or "").strip()


def using_postgres():
    return database_url().startswith(("postgres://", "postgresql://"))


@contextmanager
def get_db():
    """연결을 열고, 성공하면 commit, 끝나면 항상 close한다."""
    if using_postgres():
        import psycopg
        from psycopg.rows import dict_row

        connection = psycopg.connect(
            database_url(),
            row_factory=dict_row,
            connect_timeout=10,
        )
    else:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(DB_PATH, timeout=10)
        connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def run(db, query, params=()):
    """SQLite(?)와 Postgres(%s)의 placeholder 차이를 맞춘다."""
    if using_postgres():
        query = query.replace("?", "%s")
    return db.execute(query, params)


def is_duplicate_error(error):
    if isinstance(error, sqlite3.IntegrityError):
        return True
    return type(error).__name__ == "UniqueViolation"


def init_db():
    id_column = (
        "id BIGSERIAL PRIMARY KEY"
        if using_postgres()
        else "id INTEGER PRIMARY KEY AUTOINCREMENT"
    )

    with get_db() as db:
        run(db, f"""
            CREATE TABLE IF NOT EXISTS users (
                {id_column},
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
            row = run(
                db,
                """
                INSERT INTO users
                    (email, password_hash, created_at)
                VALUES (?, ?, ?)
                RETURNING id
                """,
                (
                    email,
                    password_hash,
                    datetime.now(timezone.utc).isoformat(),
                ),
            ).fetchone()
            user_id = row["id"]

    except Exception as error:
        if is_duplicate_error(error):
            raise HTTPException(
                status_code=409,
                detail="This email is already registered.",
            )
        raise

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
        user = run(
            db,
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

    init_db()

    with get_db() as db:
        user = run(
            db,
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
