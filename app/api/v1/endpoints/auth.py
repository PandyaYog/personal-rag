from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

from app.schemas import user as user_schema, token as token_schema
from app.services import user_service
from app.utils import security
from app.db.session import get_db
from app.core.config import settings

router = APIRouter()

# --- Email Configuration ---
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS
)

async def send_verification_email(email: str, token: str):
    """
    Sends an email using fastapi-mail.
    """
    verification_link = f"{settings.FRONTEND_URL}/confirm-email?token={token}"
    
    html = f"""
    <h2>Welcome to Personal RAG System!</h2>
    <p>Please verify your email address by clicking on the link below:</p>
    <a href="{verification_link}">Verify Email</a>
    <br><br>
    <p>If you did not request this, please ignore this email.</p>
    """

    message = MessageSchema(
        subject="Please verify your email address",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )
    
    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        print(f"Verification email sent to {email}")
    except Exception as e:
        print(f"Failed to send email to {email}. Error: {e}")

async def send_password_reset_email(email: str, token: str):
    """
    Sends a password reset email using fastapi-mail.
    """
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    html = f"""
    <h2>Password Reset Request</h2>
    <p>You requested to reset your password. Click the link below to set a new password:</p>
    <a href="{reset_link}">Reset Password</a>
    <br><br>
    <p>This link will expire in 15 minutes.</p>
    <p>If you did not request a password reset, please ignore this email.</p>
    """

    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )
    
    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        print(f"Password reset email sent to {email}")
    except Exception as e:
        print(f"Failed to send password reset email to {email}. Error: {e}")

@router.post("/forgot-password")
def forgot_password(
    request: user_schema.ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Initiates the password reset flow. 
    Returns a generic message regardless of whether the email exists.
    """
    user = user_service.get_user_by_email(db, email=request.email)
    
    if user:
        token = security.generate_password_reset_token(user.email)
        
        if settings.MAIL_SERVER:
            background_tasks.add_task(send_password_reset_email, user.email, token)
        else:
            print(f"WARNING: MAIL_SERVER not configured. Skipping password reset email to {user.email}. Token: {token}")

    return {"message": "If an account exists for that email, we have sent a password reset link."}

@router.post("/reset-password")
def reset_password(
    request: user_schema.ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Resets the user's password using the token received via email.
    """
    email = security.verify_password_reset_token(request.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid or expired password reset token."
        )
        
    user = user_service.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    user.hashed_password = security.get_password_hash(request.new_password)
    db.add(user)
    db.commit()
    
    return {"message": "Password has been reset successfully."}



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
    
    # We must be careful not to trigger exceptions if SMTP isn't configured properly during tests
    if settings.MAIL_SERVER:
        background_tasks.add_task(send_verification_email, user.email, token)
    else:
        print(f"WARNING: MAIL_SERVER not configured. Skipping email to {user.email}. Verification token: {token}")
    
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