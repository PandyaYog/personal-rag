import uuid
from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True) 
    full_name = Column(String, index=True)
    is_active = Column(Boolean(), default=True)
    is_verified = Column(Boolean(), default=False) 
    
    # We can add more fields like profile picture URL, etc. later