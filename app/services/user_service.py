from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests
import uuid
from app.db.models.user import User
from app.schemas.user import UserCreate
from app.utils.security import get_password_hash
from app.core.config import settings

# --- Getters ---
def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()

def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()

# --- Manual User Creation ---
def create_user(db: Session, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_verified=False 
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Google User Creation/Linking ---
def create_or_link_google_user(db: Session, token: str) -> User | None:
    """
    Verifies Google ID token, then creates a new user or links to an existing one.
    """
    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request())
        
        email = idinfo['email']
        full_name = idinfo.get('name')

        db_user = get_user_by_email(db, email=email)

        if db_user:
            if not db_user.is_verified:
                db_user.is_verified = True
            if not db_user.full_name and full_name:
                db_user.full_name = full_name
        else:
            base_username = email.split('@')[0].replace('.', '_').replace('+', '_')
            temp_username = base_username
            i = 1
            while get_user_by_username(db, username=temp_username):
                temp_username = f"{base_username}{i}"
                i += 1
            
            db_user = User(
                username=temp_username,
                email=email,
                full_name=full_name,
                is_verified=True, 
                hashed_password=None 
            )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    except ValueError:
        return None

# --- Verification Logic ---
def verify_user_email(db: Session, user: User) -> User:
    """Marks a user's email as verified."""
    user.is_verified = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return user