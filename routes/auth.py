from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import jwt
from passlib.hash import bcrypt
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth")

SECRET_KEY = "YOUR_SECRET_KEY"
ALGORITHM = "HS256"
fake_users_db = {}
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

class User(BaseModel):
    email: str
    phone: str
    password: str

@router.post("/register")
async def register_user(user: User):
    if user.email in fake_users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    fake_users_db[user.email] = {
        "phone": user.phone,
        "password": bcrypt.hash(user.password),
    }
    return {"message": "User registered successfully"}

@router.post("/login")
async def login(email: str, password: str):
    if email not in fake_users_db:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    stored_user = fake_users_db[email]
    if not bcrypt.verify(password, stored_user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect password")

    payload = {
        "sub": email,
        "exp": datetime.utcnow() + timedelta(minutes=30),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token}

def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/me")
async def read_me(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    return {"email": payload["sub"]}from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import jwt
from passlib.hash import bcrypt
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth")

SECRET_KEY = "YOUR_SECRET_KEY"
ALGORITHM = "HS256"
fake_users_db = {}
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

class User(BaseModel):
    email: str
    phone: str
    password: str

@router.post("/register")
async def register_user(user: User):
    if user.email in fake_users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    fake_users_db[user.email] = {
        "phone": user.phone,
        "password": bcrypt.hash(user.password),
    }
    return {"message": "User registered successfully"}

@router.post("/login")
async def login(email: str, password: str):
    if email not in fake_users_db:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    stored_user = fake_users_db[email]
    if not bcrypt.verify(password, stored_user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect password")

    payload = {
        "sub": email,
        "exp": datetime.utcnow() + timedelta(minutes=30),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token}

def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/me")
async def read_me(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    return {"email": payload["sub"]}