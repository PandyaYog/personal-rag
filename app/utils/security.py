from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import JWTError, jwt
from app.core.config import settings

# Password Hashing Context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Password Functions ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- JWT Access Token Functions ---
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, settings.APP_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# --- Special Purpose Token Functions (Email Verification / Password Reset) ---
def generate_email_verification_token(email: str) -> str:
    """Generates a short-lived JWT for email verification."""
    expires = timedelta(hours=24) 
    to_encode = {
        "exp": datetime.now(timezone.utc) + expires,
        "iat": datetime.now(timezone.utc),
        "sub": email,
        "scope": "email_verification"
    }
    return jwt.encode(to_encode, settings.APP_SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_email_verification_token(token: str) -> str | None:
    """Verifies the email verification token and returns the email."""
    try:
        payload = jwt.decode(token, settings.APP_SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("scope") == "email_verification":
            return payload.get("sub")
        return None
    except JWTError:
        return None

def generate_password_reset_token(email: str) -> str:
    """
    Generates a short-lived JWT for password reset.
    Expires in 15 minutes for enhanced security.
    """
    expires = timedelta(minutes=15)
    to_encode = {
        "exp": datetime.now(timezone.utc) + expires,
        "iat": datetime.now(timezone.utc),
        "sub": email,
        "scope": "password_reset"
    }
    return jwt.encode(to_encode, settings.APP_SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_password_reset_token(token: str) -> str | None:
    """
    Verifies the password reset token and returns the email if valid.
    Returns None if token is invalid, expired, or has the wrong scope.
    """
    try:
        payload = jwt.decode(token, settings.APP_SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("scope") == "password_reset":
            return payload.get("sub")
        return None
    except JWTError:
        # Standard JWT exceptions (ExpiredSignatureError, JWTClaimsError, etc.) are caught here
        return None