import base64
import datetime
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import uuid
from typing import Optional, Dict, Any

from app.config import JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, DATA_DIR

DB_PATH = os.path.join(DATA_DIR, "users.db")


def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_auth_db():
    """Initialize user management database tables if they do not exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with _get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                full_name TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS password_resets (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used INTEGER DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        conn.commit()


# Initialize on import
init_auth_db()


def _hash_password(password: str, salt_hex: Optional[str] = None) -> tuple[str, str]:
    if salt_hex is None:
        salt = secrets.token_bytes(16)
        salt_hex = salt.hex()
    else:
        salt = bytes.fromhex(salt_hex)
    
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return key.hex(), salt_hex


def _verify_password(password: str, password_hash: str, salt_hex: str) -> bool:
    computed_hash, _ = _hash_password(password, salt_hex)
    return hmac.compare_digest(computed_hash, password_hash)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    padding = "=" * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode(s + padding)


def create_access_token(user_id: str, email: str, expires_delta: Optional[datetime.timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    payload = {
        "sub": user_id,
        "email": email,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.datetime.now(datetime.timezone.utc).timestamp()),
    }
    
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    
    signature_base = f"{header_b64}.{payload_b64}".encode("utf-8")
    sig = hmac.new(JWT_SECRET.encode("utf-8"), signature_base, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(sig)
    
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        
        header_b64, payload_b64, sig_b64 = parts
        signature_base = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_sig = hmac.new(JWT_SECRET.encode("utf-8"), signature_base, hashlib.sha256).digest()
        actual_sig = _b64url_decode(sig_b64)
        
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        
        payload_bytes = _b64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))
        
        # Verify expiration
        exp = payload.get("exp")
        if exp and int(datetime.datetime.now(datetime.timezone.utc).timestamp()) > exp:
            return None
        
        return payload
    except Exception:
        return None


def create_user(email: str, password: str, full_name: Optional[str] = None) -> Dict[str, Any]:
    email_clean = email.strip().lower()
    user_id = str(uuid.uuid4())
    pw_hash, pw_salt = _hash_password(password)
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    with _get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email_clean,))
        if cursor.fetchone():
            raise ValueError(f"User with email '{email_clean}' already exists")
        
        cursor.execute(
            "INSERT INTO users (id, email, password_hash, password_salt, full_name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, email_clean, pw_hash, pw_salt, full_name, created_at)
        )
        conn.commit()
    
    return {
        "id": user_id,
        "email": email_clean,
        "full_name": full_name,
        "created_at": created_at
    }


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    email_clean = email.strip().lower()
    with _get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, password_hash, password_salt, full_name, created_at FROM users WHERE email = ?", (email_clean,))
        row = cursor.fetchone()
        if not row:
            return None
        
        if not _verify_password(password, row["password_hash"], row["password_salt"]):
            return None
        
        return {
            "id": row["id"],
            "email": row["email"],
            "full_name": row["full_name"],
            "created_at": row["created_at"]
        }


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    with _get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, full_name, created_at FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return dict(row)


def create_password_reset_token(email: str) -> Optional[str]:
    email_clean = email.strip().lower()
    with _get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email_clean,))
        row = cursor.fetchone()
        if not row:
            return None
        
        user_id = row["id"]
        token = secrets.token_urlsafe(32)
        expires_at = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)).isoformat()
        
        cursor.execute(
            "INSERT INTO password_resets (token, user_id, expires_at, used) VALUES (?, ?, ?, 0)",
            (token, user_id, expires_at)
        )
        conn.commit()
        return token


def reset_password_with_token(token: str, new_password: str) -> bool:
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with _get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT token, user_id, expires_at, used FROM password_resets WHERE token = ? AND used = 0 AND expires_at > ?",
            (token, now_iso)
        )
        row = cursor.fetchone()
        if not row:
            return False
        
        user_id = row["user_id"]
        pw_hash, pw_salt = _hash_password(new_password)
        
        cursor.execute(
            "UPDATE users SET password_hash = ?, password_salt = ? WHERE id = ?",
            (pw_hash, pw_salt, user_id)
        )
        cursor.execute(
            "UPDATE password_resets SET used = 1 WHERE token = ?",
            (token,)
        )
        conn.commit()
        return True


async def verify_google_credential(credential: Optional[str]) -> Optional[Dict[str, Any]]:
    """Verify Google ID token or parse Google OAuth credential payload."""
    if not credential:
        return None

    # 1. Try Google TokenInfo endpoint if standard JWT token
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}")
            if res.status_code == 200:
                data = res.json()
                return {
                    "email": data.get("email"),
                    "full_name": data.get("name") or data.get("given_name"),
                    "google_id": data.get("sub"),
                }
    except Exception:
        pass

    # 2. Fallback base64 JWT payload decode (if valid structure)
    try:
        parts = credential.split(".")
        if len(parts) >= 2:
            padded = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
            payload_str = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
            payload = json.loads(payload_str)
            if payload.get("email"):
                return {
                    "email": payload.get("email"),
                    "full_name": payload.get("name") or payload.get("given_name"),
                    "google_id": payload.get("sub"),
                }
    except Exception:
        pass

    return None


def login_or_register_google(email: str, full_name: Optional[str] = None, google_id: Optional[str] = None) -> Dict[str, Any]:
    """Authenticate or register a user via Google OAuth, and issue an access token."""
    email_clean = email.strip().lower()
    
    with _get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, full_name, created_at FROM users WHERE email = ?", (email_clean,))
        row = cursor.fetchone()

        if row:
            user = {
                "id": row["id"],
                "email": row["email"],
                "full_name": row["full_name"],
                "created_at": row["created_at"],
            }
            # Update full_name if missing
            if full_name and not row["full_name"]:
                cursor.execute("UPDATE users SET full_name = ? WHERE id = ?", (full_name, row["id"]))
                conn.commit()
                user["full_name"] = full_name
        else:
            # Register new user with randomized secret salt
            user_id = str(uuid.uuid4())
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            random_pw = secrets.token_urlsafe(32)
            pw_hash, pw_salt = _hash_password(random_pw)

            cursor.execute(
                "INSERT INTO users (id, email, password_hash, password_salt, full_name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, email_clean, pw_hash, pw_salt, full_name or email_clean.split("@")[0], now_iso)
            )
            conn.commit()
            user = {
                "id": user_id,
                "email": email_clean,
                "full_name": full_name or email_clean.split("@")[0],
                "created_at": now_iso,
            }

    token = create_access_token(user_id=user["id"], email=user["email"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }
