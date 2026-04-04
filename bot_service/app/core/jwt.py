from jose import jwt, JWTError, ExpiredSignatureError
from app.core.config import settings

def decode_and_validate(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        return payload
    except ExpiredSignatureError:
        raise ValueError("Token expired")
    except JWTError:
        raise ValueError("Invalid token")