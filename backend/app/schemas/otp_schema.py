from pydantic import BaseModel, EmailStr

class VerifyOTPSchema(BaseModel):
    email: EmailStr
    otp: str