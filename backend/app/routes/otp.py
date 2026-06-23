from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.otp import OTPCode
from app.schemas.otp_schema import VerifyOTPSchema

# Create router instance
router = APIRouter(tags=["otp"])

@router.post("/verify-otp")
def verify_otp(data: VerifyOTPSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    otp_record = db.query(OTPCode).filter(
        OTPCode.user_id == user.id,
        OTPCode.otp == data.otp
    ).first()
    
    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    if otp_record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired")
    
    user.is_verified = True
    db.commit()
    
    return {"message": "Email verified successfully"}