from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, Float, cast
from typing import Optional
from database import get_db
from models import Employee, HR
import datetime
from security import get_current_user

filter_router = APIRouter()

@filter_router.get("/employees")
async def filter_employees(
    gender: Optional[str] = Query(None, description="Filter by gender (e.g., 'M', 'F')"),
    department: Optional[str] = Query(None, description="Filter by department"),
    age: Optional[int] = Query(None, description="Exact age"),
    min_age: Optional[int] = Query(None, description="Minimum age"),
    max_age: Optional[int] = Query(None, description="Maximum age"),
    weight: Optional[float] = Query(None, description="Exact weight in kg"),
    min_weight: Optional[float] = Query(None, description="Minimum weight in kg"),
    max_weight: Optional[float] = Query(None, description="Maximum weight in kg"),
    db: AsyncSession = Depends(get_db),
    user_and_role: tuple = Depends(get_current_user)
):
    current_user, role = user_and_role
    query = select(Employee)
    
    # Isolate data so HR users only see their own organization's employees
    if role == "hr":
        query = query.where(Employee.org_id == current_user.org_id)
    else:
        # If there are other roles without org_id access, block them or handle accordingly
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only HR users can filter employees")

    
    # 1. Gender
    if gender:
        query = query.where(Employee.gender == gender)
        
    # 2. Department
    if department:
        query = query.where(Employee.department == department)
        
    # 3. Age
    if age is not None or min_age is not None or max_age is not None:
        # Postgres date_part('year', age(dob))
        age_expr = func.date_part('year', func.age(Employee.dob))
        
        if age is not None:
            query = query.where(age_expr == age)
        if min_age is not None:
            query = query.where(age_expr >= min_age)
        if max_age is not None:
            query = query.where(age_expr <= max_age)
            
    # 4. Weight (extracted from health JSONB column)
    if weight is not None or min_weight is not None or max_weight is not None:
        # Cast the JSONB field value to Float for numeric comparison
        weight_expr = cast(Employee.health['weight_kg'].astext, Float)
        
        if weight is not None:
            query = query.where(weight_expr == weight)
        if min_weight is not None:
            query = query.where(weight_expr >= min_weight)
        if max_weight is not None:
            query = query.where(weight_expr <= max_weight)
            
    # Execute query
    result = await db.execute(query)
    employees = result.scalars().all()
    
    from datetime import date
    today = date.today()
    return {
        "count": len(employees), 
        "employees": [
            {
                "name": emp.name, 
                "department": emp.department, 
                "gender": emp.gender,
                "age": today.year - emp.dob.year - ((today.month, today.day) < (emp.dob.month, emp.dob.day)) if emp.dob else None
            } 
            for emp in employees
        ]
    }
