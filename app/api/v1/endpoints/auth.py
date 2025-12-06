from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.schemas import user as user_schema, token as token_schema
from app.services import user_service
from app.utils import security
from app.db.session import get_db

router = APIRouter()

# --- Mock Email Sending Function ---
def send_verification_email(email: str, token: str):
    """
    Simulates sending an email. In a real app, this would use a service like SendGrid or SMTP.
    For this project, we'll just print it to the console.
    """
    verification_link = f"http://localhost:8000/v1/auth/confirm-email?token={token}" # Example link
    print("---- SENDING VERIFICATION EMAIL ----")
    print(f"To: {email}")
    print(f"Subject: Please verify your email address")
    print(f"Click the link to verify: {verification_link}")
    print("------------------------------------")


@router.post("/signup", response_model=user_schema.User, status_code=status.HTTP_201_CREATED)
def signup(
    user_in: user_schema.UserCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle new user registration. A verification email will be 'sent'.
    """
    if user_service.get_user_by_email(db, email=user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if user_service.get_user_by_username(db, username=user_in.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    
    user = user_service.create_user(db=db, user=user_in)
    
    token = security.generate_email_verification_token(user.email)
    background_tasks.add_task(send_verification_email, user.email, token)
    
    return user

@router.post("/signup/google", response_model=token_schema.Token)
def signup_google(
    token_in: user_schema.GoogleIdToken, 
    db: Session = Depends(get_db)
):
    """
    Handles user creation/login via a Google ID Token.
    Verifies the token, creates/links the user, and returns a JWT.
    """
    user = user_service.create_or_link_google_user(db, token=token_in.id_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid Google token."
        )
    
    access_token = security.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/confirm-email")
def confirm_email(token: str, db: Session = Depends(get_db)):
    """
    Verify the email address from the link sent to the user.
    """
    email = security.verify_email_verification_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token.")
    
    user = user_service.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.is_verified:
        return {"message": "Email already verified."}
        
    user_service.verify_user_email(db, user=user)
    return {"message": "Email verified successfully. You can now log in."}

@router.post("/token", response_model=token_schema.Token)
def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = user_service.get_user_by_username(db, username=form_data.username)
    if not user:
        user = user_service.get_user_by_email(db, email=form_data.username)

    if not user or not user.hashed_password or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Email not verified. Please check your inbox for a verification link."
        )
        
    access_token = security.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}