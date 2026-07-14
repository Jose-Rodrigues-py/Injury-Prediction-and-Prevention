from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from security import get_current_user
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Athlete, Race
from datetime import datetime, timezone, timedelta

router = APIRouter()

class RaceCreate(BaseModel):
    goal: str | None = None
    distance: float
    date: datetime

@router.get("/races/myraces")
async def get_races(athlete: Athlete = Depends(get_current_user), db: AsyncSession = Depends(get_db)): 
    query = (
        select(Race)
        .where(Race.athlete_id == athlete.id)
        .order_by(Race.date.asc())
    )
    result = await db.execute(query)
    info = result.scalars().all()

    return info

@router.post("/races/addrace")
async def add_race(info: RaceCreate, athlete: Athlete = Depends(get_current_user), db: AsyncSession = Depends(get_db)): 
    to_add = Race(
        goal = info.goal,
        distance = info.distance,
        date = info.date,
        athlete_id = athlete.id
    )

    db.add(to_add)
    await db.commit()
    await db.refresh(to_add)

    return {"Message": " new race added ",
            "data": {"goal": info.goal,
                     "distance": info.distance,
                     "date": info.date
                     }
            }