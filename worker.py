"""
Handles background jobs
"""
from arq.connections import RedisSettings
from predict import predict_injury_risk
from database import AsyncSessionLocal
import json
from cache import redis_client

async def run_prediction(ctx, athlete_id: int):
    async with AsyncSessionLocal() as db:
        result = await predict_injury_risk(athlete_id, db)
        await redis_client.set(f"risk:{athlete_id}", json.dumps(result))
        return result

class WorkerSettings:
    functions = [run_prediction]
    redis_settings = RedisSettings(host="localhost", port=6379)