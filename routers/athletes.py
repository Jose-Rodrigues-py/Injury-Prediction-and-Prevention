from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from security import create_token, hash_password, verify, get_current_user
from database import get_db
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Athlete

router = APIRouter()

@router.get("/athlete/me")
async def get_user(athlete: Athlete = Depends(get_current_user)):
    return {"name": athlete.name, "id": athlete.id, "email": athlete.email}

class addInfo(BaseModel): 
    height: int
    age: int

@router.post("/athlete/me/information")
async def add_info(data: addInfo, athlete: Athlete = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    athlete.height = data.height
    athlete.age = data.age  
    
    await db.commit()
    await db.refresh(athlete)
    
    return {"message": "new information added",
            "data": {"age": athlete.age, "height": athlete.height}}
    
