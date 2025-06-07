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
from utils import generate_otp,store_otp,send_email_otp,verify_otp

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
    email: EmailStr

class VerifyOtpRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    otp: str




@app.post("/api/start-registration")
def start_registration(request: StartRegistrationRequest):
    otp = generate_otp()
    store_otp(request.email, otp)
    status_code = send_email_otp(request.email, otp)

    if status_code != 202:
        raise HTTPException(status_code=500, detail="Failed to send OTP email")

    return {"message": "OTP sent to your email."}

@app.post("/api/verify-otp")
def verify_otp_and_register(request: VerifyOtpRequest, db: Session = Depends(get_db)):
    # Check if OTP is valid
    if not verify_otp(request.email, request.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    # Check if username already exists
    existing_user = db.query(Seller).filter(Seller.username == request.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

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

    return {"message": "Seller registered successfully!"}

@app.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    if user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = pwd_context.hash(request.password)
    new_user = User(username=request.username, email=request.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully"}

@app.post("/login")
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


# @app.post("/seller-register")
# def register(request: RegisterRequest, db: Session = Depends(get_db)):
#     user = db.query(Seller).filter(Seller.username == request.username).first()
#     if user:
#         raise HTTPException(status_code=400, detail="Username already registered")
#     hashed_password = pwd_context.hash(request.password)
#     new_user = Seller(username=request.username, email=request.email, hashed_password=hashed_password)
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)
#     return {"message": "seller registered successfully"}

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
