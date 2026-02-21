from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import DBUser, HR, Employee, Org

import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_jwt_from_header(authorization: str) -> dict:
    """Extract and decode JWT from Authorization header"""
    if not authorization:
        raise ValueError("Missing authorization header")
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise ValueError("Invalid authorization header format")
    
    token = parts[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid token: {str(e)}")

async def decode_user_id_from_jwt(payload: dict, db: AsyncSession) -> tuple:
    """Decode user info from JWT payload"""
    identifier = payload.get("sub")
    role = payload.get("role")
    
    if not identifier:
        raise ValueError("Invalid token payload")
    
    if role == "hr":
        result = await db.execute(select(HR).where(HR.email == identifier))
        user = result.scalar()
    elif role == "employee":
        result = await db.execute(select(Employee).where(Employee.email == identifier))
        user = result.scalar()
    elif role == "org":
        result = await db.execute(select(Org).where(Org.name == identifier))
        user = result.scalar()
    else:
        # Fallback to standard DBUser
        result = await db.execute(select(DBUser).where((DBUser.username == identifier) | (DBUser.email == identifier)))
        user = result.scalar()
    
    if not user:
        raise ValueError(f"User not found for identifier: {identifier}")
    
    return user, role

from database import get_db

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> tuple:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise credentials_exception
    
    try:
        user, role = await decode_user_id_from_jwt(payload, db)
    except ValueError:
        raise credentials_exception
        
    return user, role

class RoleChecker:
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    def __call__(self, user_and_role: tuple = Depends(get_current_user)):
        user, role = user_and_role
        if role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
        return user
