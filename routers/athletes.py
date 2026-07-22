from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from security import get_current_user
from database import get_db
from sqlalchemy import select
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
    training_age: int
    baseline: int # how many kms has the athlete logged in the past year (check your watch's app)

@router.post("/athlete/me/information")
async def add_info(data: addInfo, current: Athlete = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Athlete).where(Athlete.id == current.id))
    athlete = result.scalar_one_or_none()

    if athlete is None:
        raise HTTPException(status_code=401, detail="No athlete found with given id")
    
    athlete.height = data.height
    athlete.age = data.age  
    athlete.training_age_years = data.training_age
    athlete.baseline_load = data.baseline
    
    await db.commit()
    await db.refresh(athlete)
    await redis_client.delete(f"id:{athlete.id}")
    
    return {"message": "new information added",
            "data": {"age": athlete.age, "height": athlete.height, "experience": athlete.training_age, "baseline": athlete.baseline_load}}
    
