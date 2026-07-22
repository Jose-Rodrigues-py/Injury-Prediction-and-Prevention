from fastapi import APIRouter, Depends
from security import get_current_user
from models import Athlete
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from predict import predict_injury_risk

router = APIRouter()

@router.post("/predict")
async def predict(user: Athlete = Depends(get_current_user), db: AsyncSession = Depends(get_db)): 
    user_id = user.id
    result = await predict_injury_risk(user_id, db)
    return {"athlete_id": result["athlete_id"],
            "healthy": 1 - result["injury_risk_probability"],
            "acwr": result["acwr"],
            "tsb": result["tsb"],
            "ctl": result["ctl"],
            "atl": result["atl"]
            }
