import asyncio
from sqlalchemy import text
from database import SessionLocal

async def main():
    async with SessionLocal() as db:
        await db.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS summary VARCHAR;"))
        await db.commit()
        print("Done")

if __name__ == "__main__":
    asyncio.run(main())
