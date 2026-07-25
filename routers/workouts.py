from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from enum import Enum
from security import get_current_user
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Athlete, Workout
from datetime import date

router = APIRouter()

class SessionEnum(str, Enum): 
    recovery ='recovery'
    easy = "easy_run"
    long = "long_run"
    tempo = "tempo"
    intervals = "intervals"
    race = "race"

class Data(BaseModel): 
    session_type: SessionEnum # show options to the user, no need to write
    duration: int = Field(ge=0 , description="Duration in minutes")
    intensity: int = Field(gt=0, le=10)
    speed: float
    average_hr: int
    rpe: int = Field(ge=0, le=10)

@router.post("/workouts/addwourkout")
async def add_workout(data: Data, request: Request, athlete: Athlete = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    to_add = Workout(
        session_type = data.session_type,
        date = date.today(),
        athlete_id = athlete.id,
        duration = data.duration,
        intensity = data.intensity,
        speed = data.speed,
        average_hr = data.average_hr,
        rpe = data.rpe
    )

    db.add(to_add)
    await db.commit()
    await db.refresh(to_add)
    # add line here?? (prevent stale entries in cache)
    await request.app.state.arq_pool.enqueue_job("run_prediction", athlete.id)

    return {"message": "new workout added",
            "data": {"session_type": data.session_type,
                    "athlete_id": athlete.id,
                    "date": date.today(),
                    "duration": data.duration,
                    "intensity": data.intensity,
                    "speed": data.speed,
                    "average_hr": data.average_hr,
                    "rpe": data.rpe
                    }
            }

@router.get("/workouts/myworkouts-all")
async def get_workouts(athlete: Athlete = Depends(get_current_user), db: AsyncSession = Depends(get_db), 
                       speed: int = None, rpe: int = None, duration: int = None, intensity: int = None, hr: int = None, type: str = None):
    
    query = (
        select(Workout)
        .where(Workout.athlete_id == athlete.id)
        .order_by(Workout.date.desc())
    )

    if speed: 
        query.where(Workout.speed >= speed)
    if rpe: 
        query.where(Workout.rpe >= rpe)
    if duration:
        query.where(Workout.duration >= duration)
    if intensity:
        query.where(Workout.intensity >= intensity)        
    if hr:
        query.where(Workout.average_hr >= hr)
    if type:
        query.where(Workout.session_type == type)

    result = await db.execute(query)
    info = result.scalars().all()

    return info


