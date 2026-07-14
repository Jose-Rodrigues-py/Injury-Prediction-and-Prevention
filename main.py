from fastapi import FastAPI
from routers import auth, athletes, health_metrics

app = FastAPI()

app.include_router(auth.router, prefix="")
app.include_router(athletes.router, prefix="")
app.include_router(health_metrics.router, prefix="")

