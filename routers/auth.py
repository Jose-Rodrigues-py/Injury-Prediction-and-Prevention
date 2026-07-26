from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
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
async def signin(data: SignIn, db: AsyncSession = Depends(get_db)):
    check = await db.execute(select(Athlete).where(Athlete.email == data.email))
    athlete = check.scalar_one_or_none()
    if not athlete:
        raise HTTPException(status_code=401, detail="User not signed up")
    if not verify(data.password, athlete.hashed_pwd):
        raise HTTPException(status_code=401, detail="Wrong Password")
    token = create_token({"sub": str(athlete.id)})
    return {
        "message": "user signed in successfully",
        "access_token": token,
        "token_type": "bearer",
        "data": {"name": athlete.name, "email": athlete.email},  # add this so onAuthed(res.data) works
    }
