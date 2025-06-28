from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.schemas import user as user_schema
from app.db.models.user import User
from app.api.v1 import deps
from app.db.session import get_db
from app.utils import security
from app.services import user_service
from app.api.v1.endpoints.auth import send_verification_email

router = APIRouter()

@router.get("/me", response_model=user_schema.User)
def read_users_me(current_user: User = Depends(deps.get_current_active_user)):
    return current_user

@router.put("/me", response_model=user_schema.User)
def update_user_me(
    user_in: user_schema.UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Update user's full_name or username.
    """
    if user_in.username:
        if user_service.get_user_by_username(db, user_in.username):
            raise HTTPException(status_code=400, detail="Username is already taken.")
        current_user.username = user_in.username

    if user_in.full_name is not None:
        current_user.full_name = user_in.full_name

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.put("/me/change-password", status_code=status.HTTP_200_OK)
def change_password(
    passwords: user_schema.PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    if not current_user.hashed_password:
        raise HTTPException(status_code=400, detail="Cannot change password for Google-only account.")
    if not security.verify_password(passwords.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password.")
    
    current_user.hashed_password = security.get_password_hash(passwords.new_password)
    db.add(current_user)
    db.commit()
    
    return {"message": "Password updated successfully."}

@router.put("/me/change-email", status_code=status.HTTP_200_OK)
def change_email(
    email_in: user_schema.EmailUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Allows a user to change their email. Requires password verification.
    The new email will require re-verification.
    """
    if not current_user.hashed_password or not security.verify_password(email_in.password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password.")
    if user_service.get_user_by_email(db, email=email_in.new_email):
        raise HTTPException(status_code=400, detail="This email is already registered.")

    current_user.email = email_in.new_email
    current_user.is_verified = False # MUST re-verify
    db.add(current_user)
    db.commit()

    # Send verification to the new email
    token = security.generate_email_verification_token(email_in.new_email)
    background_tasks.add_task(send_verification_email, email_in.new_email, token)

    return {"message": "Email change requested. Please check your new email address to verify."}