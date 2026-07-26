from fastapi import FastAPI
from routers import auth, athletes, health_metrics, races, workouts, predict_risk, ai_agent
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from arq import create_pool
from arq.connections import RedisSettings

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.arq_pool = await create_pool(RedisSettings(host="localhost", port=6379))
    yield
    await app.state.arq_pool.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # fine for local dev; restrict this in real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="")
app.include_router(athletes.router, prefix="")
app.include_router(health_metrics.router, prefix="")
app.include_router(races.router, prefix="")
app.include_router(workouts.router, prefix="")
app.include_router(predict_risk.router, prefix="")
app.include_router(ai_agent.router, prefix="")
