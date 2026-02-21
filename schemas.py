from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel): # Renamed from User to avoid confusion with DB model
    username: str
    email: EmailStr
    password: str
    phone_number: str

class LoginRequest(BaseModel):
    username_or_email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str = "user"

class employeeProfile(BaseModel):
    employee_id: int
    gender: str
    age: int
    weight: int
    Regular_exercise: bool
    