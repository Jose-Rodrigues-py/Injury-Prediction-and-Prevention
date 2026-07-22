from fastapi import FastAPI
from routers import auth, athletes, health_metrics, races, workouts, predict_risk

app = FastAPI()

app.include_router(auth.router, prefix="")
app.include_router(athletes.router, prefix="")
app.include_router(health_metrics.router, prefix="")
app.include_router(races.router, prefix="")
app.include_router(workouts.router, prefix="")
app.include_router(predict_risk.router)
