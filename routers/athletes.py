from fastapi import APIRouter, Depends
from pydantic import BaseModel
from security import get_current_user
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from models import Athlete
from cache import redis_client

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
    await redis_client.delete(f"id:{athlete.id}")
    
    return {"message": "new information added",
            "data": {"age": athlete.age, "height": athlete.height}}
    
