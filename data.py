from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import HR, EmployeeProfile
from security import get_current_user, oauth2_scheme
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

@data_router.get("/user")
async def get_all_employees(
    db: AsyncSession = Depends(get_db),
    user_and_role: tuple = Depends(get_current_user)
):
    current_user, role = user_and_role

    # Check if the user is an HR
    if role != "hr":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only HR users can access this endpoint")

    # Fetch organization name
    org_query = select(HR).where(HR.org_id == current_user.org_id)
    org_result = await db.execute(org_query)
    organization = org_result.scalars().first()

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    return {
        "current_user": current_user.name,
        "organization_id": current_user.org_id
    }
