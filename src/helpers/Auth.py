from datetime import datetime, timedelta, timezone

import bcrypt
import jwt


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_token(secret: str, expire_days: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(days=expire_days)
    return jwt.encode({"exp": exp}, secret, algorithm="HS256")


def verify_token(token: str, secret: str) -> bool:
    try:
        jwt.decode(token, secret, algorithms=["HS256"])
        return True
    except jwt.PyJWTError:
        return False
