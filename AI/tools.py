"""
defines all the tools the agent will be able to use
"""
from predict import predict_injury_risk
from database import AsyncSessionLocal
from cache import redis_client
from sqlalchemy import select
from rag import search
from models import Workout, Race, HealthMetrics, Message
from datetime import date, datetime
import json


async def make_prediction(athlete_id: int): 
    async with AsyncSessionLocal() as db:
        result = await predict_injury_risk(athlete_id, db)
        await redis_client.set(f"risk:{athlete_id}", json.dumps(result))
        return result

async def get_message_history(user_id: int, limit: int = 20) -> list[Message]:
    async with AsyncSessionLocal() as db:
        query = (select(Message).where(Message.athlete_id == user_id).order_by(Message.created_at.desc()).limit(limit))
        result = await db.execute(query)
        return list(reversed(result.scalars().all()))

async def save_message(user_id: int, role: str, content: str) -> None:
    async with AsyncSessionLocal() as db:
        msg = Message(athlete_id=user_id, role=role, content=content)
        db.add(msg)
        await db.commit()

def row_to_dict(obj, fields: list[str]) -> dict:
    result = {}
    for f in fields:
        value = getattr(obj, f)
        if isinstance(value, (date, datetime)):
            value = str(value)
        result[f] = value
    return result

async def access_db(user_id: int):
    cached = await redis_client.get(f"user_context:{user_id}")
    if cached:
        return json.loads(cached)

    async with AsyncSessionLocal() as db:
        workout_result = await db.execute(select(Workout).where(Workout.athlete_id == user_id).order_by(Workout.date.desc()).limit(42))
        race_result = await db.execute(select(Race).where(Race.athlete_id == user_id).order_by(Race.date.desc()).limit(5))
        metrics_result = await db.execute(select(HealthMetrics).where(HealthMetrics.athlete_id == user_id).order_by(HealthMetrics.created_at.desc()).limit(42))

        ans = {
            "workouts": [
                row_to_dict(w, ["date", "session_type", "duration", "intensity", "rpe", "speed", "average_hr"])
                for w in workout_result.scalars().all()
            ],
            "races": [
                row_to_dict(r, ["date", "distance", "goal"])
                for r in race_result.scalars().all()
            ],
            "metrics": [
                row_to_dict(m, ["created_at", "resting_hr", "weight", "hrv", "mood"])
                for m in metrics_result.scalars().all()
            ]
        }

    await redis_client.set(f"user_context:{user_id}", json.dumps(ans), ex=300)  # 5 min TTL
    return ans