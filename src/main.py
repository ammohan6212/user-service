from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, User
from passlib.context import CryptContext
from auth import create_access_token
from pydantic import BaseModel
from datetime import datetime, timedelta
import secrets
from fastapi.responses import RedirectResponse
from httpx import post

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

GO_BACKEND_URL = "http://localhost:8000/products"

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
    try:
        go_backend_url = "http://localhost:8000/api/products"  # Replace with actual URL or service name
        payload = {
            "username": user.username,
            "status": "logged_in"
        }
        post(go_backend_url, json=payload)
    except Exception as e:
        print(f"Failed to notify Go backend: {e}")  # Optional: log the error

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer"
    }


