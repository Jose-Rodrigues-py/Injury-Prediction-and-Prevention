from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from security import get_current_user
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Athlete, HealthMetrics
from datetime import datetime, timezone, timedelta

router = APIRouter()

class Data(BaseModel):
    resting_hr: int | None
    weight: int | None
    hrv: int | None
    mood: int | None
    vo2_max: int | None
    lt: int | None

# missing chronic training load..

@router.post("/metrics/add")
async def add_metrics(info: Data, athlete: Athlete = Depends(get_current_user), db: AsyncSession = Depends(get_db)): 
    to_add = HealthMetrics(
        athlete_id = athlete.id,
        created_at = datetime.now(timezone.utc),
        resting_hr = info.resting_hr,
        weight = info.weight,
        hrv = info.hrv,
        mood = info.mood,
        vo2_max = info.vo2_max,
        lt = info.lt
    )

    db.add(to_add)
    await db.commit()
    await db.refresh(to_add)

    return {"message": "new health metrics added",
            "athlete": athlete.id,
            "data": {"created_at": datetime.now(timezone.utc),
                    "resting_hr": info.resting_hr,
                    "weight": info.weight,
                    "hrv": info.hrv,
                    "mood": info.mood,
                    "vo2_max": info.vo2_max,
                    "lt": info.lt
                    }
            }
    
@router.get("/metrics/mydata")    
async def get_data(period: int = 7, athlete: Athlete = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    time = datetime.now() - timedelta(days=period)
    query = (
        select(HealthMetrics)
        .where(HealthMetrics.athlete_id == athlete.id)
        .where(HealthMetrics.created_at >= time)
        .order_by(HealthMetrics.created_at.desc()) # Newest information first
    )

    result = await db.execute(query)
    info = result.scalars().all()
    
    return info











    