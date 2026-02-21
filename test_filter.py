import asyncio
from sqlalchemy import select, func, cast, Float
from models import Employee
from database import get_db, SessionLocal
import datetime
import traceback
import sys

async def main():
    with open("test_filter.out", "w") as f:
        sys.stdout = f
        sys.stderr = f
        async with SessionLocal() as db:
            try:
                query = select(Employee)
                result = await db.execute(query)
                employees = result.scalars().all()
                print(f"Total employees: {len(employees)}")
                
                # test age
                age_expr = func.date_part('year', func.age(Employee.dob))
                query2 = select(Employee).where(age_expr >= 25)
                r2 = await db.execute(query2)
                print(f"Age filtered: {len(r2.scalars().all())}")

                # test weight
                weight_expr = cast(Employee.health['weight_kg'].astext, Float)
                query3 = select(Employee).where(weight_expr <= 80.0)
                r3 = await db.execute(query3)
                print(f"Weight filtered: {len(r3.scalars().all())}")
            except Exception as e:
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
