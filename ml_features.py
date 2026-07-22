from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Workout, Athlete
from features import compute_rolling_features


async def calculate_features(user_id: int, db: AsyncSession):
    today = date.today()
    window_start = today - timedelta(days=41)

    stmt = select(Workout).where(Workout.athlete_id == user_id, Workout.date >= window_start)
    athlete_stmt = select(Athlete).where(Athlete.id == user_id)

    result = await db.execute(stmt)
    workouts = result.scalars().all()
    result2 = await db.execute(athlete_stmt)
    athlete_info = result2.scalar_one_or_none()

    if athlete_info is None:
        return None

    loads_by_date = {}
    for w in workouts:
        daily_load = w.duration * w.rpe
        loads_by_date[w.date] = loads_by_date.get(w.date, 0) + daily_load

    daily_loads = []
    current = window_start
    while current <= today:
        daily_loads.append(loads_by_date.get(current, 0))
        current += timedelta(days=1)

    seed = athlete_info.baseline_load * 0.9 if athlete_info.baseline_load else None
    return compute_rolling_features(daily_loads, seed=seed)