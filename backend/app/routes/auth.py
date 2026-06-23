from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.otp import OTPCode
from app.schemas.auth_schema import SignupSchema, LoginSchema
from app.services.auth_service import hash_password, verify_password
from app.services.jwt_service import create_access_token
from app.services.otp_service import generate_otp
from app.services.email_service import send_otp_email
from app.services.auth_dependency import get_current_user

# Create router instance
router = APIRouter(tags=["auth"])

@router.post("/signup")
def signup(user: SignupSchema, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create new user
    new_user = User(
        name=user.name,
        email=user.email,
        password_hash=hash_password(user.password),
        is_verified=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate and store OTP
    otp = generate_otp()
    otp_record = OTPCode(
        user_id=new_user.id,
        otp=otp,
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )
    
    db.add(otp_record)
    db.commit()
    
    # Send OTP email (async, non-blocking)
    send_otp_email(new_user.email, otp, new_user.name)
    
    # Always return OTP in response for development/testing
    # In production, you would only return this if email sending fails
    response = {
        "message": "User created successfully. Please verify your email.",
        "user_id": new_user.id,
        "otp": otp,
        "email_sent": True
    }
    
    return response

@router.post("/resend-otp")
def resend_otp(data: dict, db: Session = Depends(get_db)):
    """Resend OTP to user's email"""
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    # Generate new OTP
    otp = generate_otp()
    otp_record = OTPCode(
        user_id=user.id,
        otp=otp,
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )
    
    db.add(otp_record)
    db.commit()
    
    # Send OTP email (async, non-blocking)
    send_otp_email(user.email, otp, user.name)
    
    # Always return OTP in response
    response = {
        "message": "OTP resent successfully",
        "otp": otp,
        "email_sent": True
    }
    
    return response

@router.post("/login")
def login(user: LoginSchema, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not db_user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email first")
    
    token = create_access_token({"user_id": db_user.id, "email": db_user.email})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "name": db_user.name,
            "email": db_user.email
        }
    }

@router.get("/profile")
def get_profile(current_user = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "is_verified": current_user.is_verified,
        "created_at": current_user.created_at
    }