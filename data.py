from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import EmployeeProfile
from security import oauth2_scheme
data_router = APIRouter()

@data_router.get("/employee/profile")
async def get_employee_profile(employee_id: int, token:str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)): 
    result = await db.execute(select(EmployeeProfile).where(EmployeeProfile.employee_id == employee_id))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    return profile

@data_router.post("/employee/profile")
async def create_employee_profile(profile: EmployeeProfile, db: AsyncSession = Depends(get_db)):    
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile
