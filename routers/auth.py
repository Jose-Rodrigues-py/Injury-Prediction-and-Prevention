from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from security import create_token, hash_password, verify
from database import get_db
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Athlete

router = APIRouter()

class SignUp(BaseModel): 
    email: EmailStr
    name: str
    password: str

@router.post("/signup")
async def signup(user: SignUp, db: AsyncSession = Depends(get_db)):
    athlete_email = user.email
    check = await db.execute(select(Athlete).where(Athlete.email == athlete_email))

    athlete = check.scalar_one_or_none()

    if athlete: 
        raise HTTPException(status_code=401, detail =  "User already signed up")

    else:
        pwd = hash_password(user.password)
        new_athlete = Athlete(
            name = user.name,
            email = user.email, 
            hashed_pwd = pwd
        )
        db.add(new_athlete)
        await db.commit()
        await db.refresh(new_athlete)
        
        return {"message": "user created",
                "data": {"name": user.name, "email": user.email}}

class SignIn(BaseModel): 
    email: EmailStr
    password: str

@router.post("/signin")
async def signin(user: SignIn, db: AsyncSession = Depends(get_db)): 
    check = await db.execute(select(Athlete).where(Athlete.email == user.email))    
    athlete = check.scalar_one_or_none()
    if not athlete: 
        raise HTTPException(status_code=401, detail = "User not signed up")
    else: 
        if not verify(user.password, athlete.hashed_pwd):
            raise HTTPException(status_code=401, detail="Wrong Password")
        else: 
            token = create_token({"sub": athlete.id})
            return {"message": "user signed in successfully",
                    "data": token}

