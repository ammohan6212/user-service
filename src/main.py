from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, User,Seller
from passlib.context import CryptContext
from auth import create_access_token
from pydantic import BaseModel,EmailStr
from datetime import datetime, timedelta
import secrets
from fastapi.responses import RedirectResponse
from httpx import post
from utils import generate_otp,store_otp,send_email_otp_gmail,verify_otp

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from fastapi.middleware.cors import CORSMiddleware

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class StartRegistrationRequest(BaseModel):
    username: str
    email: EmailStr


class VerifyOtpRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    otp: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyForgotPasswordOtpRequest(BaseModel):
    email: EmailStr
    otp: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str


@app.post("/start-seller-registration")
def start_registration(request: StartRegistrationRequest, db: Session = Depends(get_db)):
    # 1️⃣ Check if email already registered
    existing_user = db.query(Seller).filter(Seller.username == request.username).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Username already registered")
    
    existing_email = db.query(Seller).filter(Seller.email == request.email).first()
    if existing_email:
        raise HTTPException(status_code=409, detail="Email already registered")

    # 2️⃣ Generate OTP and store it
    otp = generate_otp()
    store_otp(request.email, otp)

    # 3️⃣ Send OTP via email
    status_code = send_email_otp_gmail(request.email, otp)
    if status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to send OTP email")

    # 4️⃣ Return success message
    return {"message": "OTP sent to your email."}


@app.post("/verify-seller-otp")
def verify_otp_and_register(request: VerifyOtpRequest, db: Session = Depends(get_db)):
    # Check if OTP is valid, don't delete yet
    # Check OTP validity (401 = Unauthorized, since OTP is part of authentication process)
    if not verify_otp(request.email, request.otp, delete_on_success=False):
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")
    # All good, now delete OTP and register seller
    verify_otp(request.email, request.otp, delete_on_success=True)

    # Register the seller
    hashed_password = pwd_context.hash(request.password)
    new_seller = Seller(
        username=request.username,
        email=request.email,
        hashed_password=hashed_password
    )
    db.add(new_seller)
    db.commit()
    db.refresh(new_seller)

    return {"message": "Sell"}

@app.post("/seller-login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Seller).filter(Seller.username == request.username).first()
    if not user or not pwd_context.verify(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.username})
    return {
        "message": " seller Login successful",
        "access_token": access_token,
        "token_type": "bearer"
    }



@app.post("/start-user-registration")
def start_user_registration(request: StartRegistrationRequest, db: Session = Depends(get_db)):
    # Check if username already registered
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Username already registered")

    # Check if email already registered
    existing_email = db.query(User).filter(User.email == request.email).first()
    if existing_email:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Generate OTP and store it
    otp = generate_otp()
    store_otp(request.email, otp)

    # Send OTP via email
    status_code = send_email_otp_gmail(request.email, otp)
    if status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to send OTP email")

    return {"message": "OTP sent to your email."}

@app.post("/verify-user-otp")
def verify_user_otp_and_register(request: VerifyOtpRequest, db: Session = Depends(get_db)):
    # Check OTP validity (401 = Unauthorized)
    if not verify_otp(request.email, request.otp, delete_on_success=False):
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")

    # Delete OTP after success
    verify_otp(request.email, request.otp, delete_on_success=True)

    # Register User
    hashed_password = pwd_context.hash(request.password)
    new_user = User(
        username=request.username,
        email=request.email,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully!"}




@app.post("/user-login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    if not user or not pwd_context.verify(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.username})
    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer"
    }


@app.post("/forgot-user-password")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # Check if email exists
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    # Generate OTP
    otp = generate_otp()
    store_otp(request.email, otp)

    # Send OTP via email
    status_code = send_email_otp_gmail(request.email, otp)
    if status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to send OTP email")

    return {"message": "OTP sent to your email."}


@app.post("/verify-user-otp")
def verify_forgot_password_otp(request: VerifyForgotPasswordOtpRequest):
    if not verify_otp(request.email, request.otp, delete_on_success=False):
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")

    # Delete OTP after success
    verify_otp(request.email, request.otp, delete_on_success=True)

    # Allow reset
    return {"message": "OTP verified. You can now reset your password."}

@app.post("/reset-user-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_password = pwd_context.hash(request.new_password)
    user.hashed_password = hashed_password
    db.commit()

    return {"message": "Password reset successfully!"}


@app.post("/seller-forgot-password")
def seller_forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    seller = db.query(Seller).filter(Seller.email == request.email).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Email not found")

    otp = generate_otp()
    store_otp(request.email, otp)

    status_code = send_email_otp_gmail(request.email, otp)
    if status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to send OTP email")

    return {"message": "OTP sent to your email."}


@app.post("/seller-verify-otp")
def seller_verify_forgot_password_otp(request: VerifyForgotPasswordOtpRequest):
    if not verify_otp(request.email, request.otp, delete_on_success=False):
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")

    verify_otp(request.email, request.otp, delete_on_success=True)

    return {"message": "OTP verified. You can now reset your password."}


@app.post("/seller-reset-password")
def seller_reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    seller = db.query(Seller).filter(Seller.email == request.email).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")

    hashed_password = pwd_context.hash(request.new_password)
    seller.hashed_password = hashed_password
    db.commit()

    return {"message": "Password reset successfully!"}