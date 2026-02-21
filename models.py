from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Date
from sqlalchemy.dialects.postgresql import JSONB
from database import Base
from sqlalchemy.orm import relationship

class DBUser(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=False)

class Org(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

class HR(Base):
    __tablename__ = "hr_users"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    hash_algorithm = Column(String, nullable=False)
    hash_rounds = Column(Integer, nullable=False)
    role = Column(String, nullable=False)

class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(String, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String)
    gender = Column(String)
    dob = Column(Date)
    department = Column(String)
    job_level = Column(String)
    location_city = Column(String)
    marital_status = Column(String)
    health = Column(JSONB)
    summary = Column(String)
