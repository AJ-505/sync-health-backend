from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from schemas import LoginRequest, UserCreate, Token
from models import DBUser, Org, HR
from security import get_password_hash, verify_password, create_access_token
from fastapi.middleware.cors import CORSMiddleware
auth_router = APIRouter()
@auth_router.post("/register")


async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if username or email exists
    result = await db.execute(
        select(DBUser).where((DBUser.email == user.email) | (DBUser.username == user.username))
    )
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username or email already registered")

    # Create new user
    hashed_pwd = get_password_hash(user.password)
    new_user = DBUser(
        username=user.username,
        email=user.email,
        phone_number=user.phone_number,
        hashed_password=hashed_pwd,
        is_active=False # They need to verify OTP first
    )
    
    db.add(new_user)
    await db.commit()
    return {"message": "User registered successfully. Please verify your phone number via OTP."}

@auth_router.post("/login", response_model=Token)
async def login_user(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = None
    role = "user"
    identifier = ""

    # Check DBUser first
    result = await db.execute(
        select(DBUser).where(
            (DBUser.username == request.username_or_email) | 
            (DBUser.email == request.username_or_email)
        )
    )
    db_user = result.scalars().first()

    if db_user and verify_password(request.password, db_user.hashed_password):
        if not db_user.is_active:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account not active. Verify OTP.")
        user = db_user
        role = "user"
        identifier = db_user.username
    else:
        # Check HR Users
        result = await db.execute(select(HR).where(HR.email == request.username_or_email))
        hr_user = result.scalars().first()
        if hr_user and verify_password(request.password, hr_user.password_hash):
            user = hr_user
            role = "hr" # could also be mapped to hr_user.role natively
            identifier = hr_user.email
            
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Generate API Token
    access_token = create_access_token(data={"sub": identifier, "role": role})
    return {"access_token": access_token, "token_type": "bearer", "role": role}