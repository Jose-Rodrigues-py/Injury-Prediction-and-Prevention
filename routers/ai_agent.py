from fastapi import APIRouter, Depends
from pydantic import BaseModel
from models import Athlete, Message
from sqlalchemy.ext.asyncio import AsyncSession
from security import get_current_user
from database import get_db
from sqlalchemy import select
from AI.agent import run_agent

router = APIRouter()

class Input(BaseModel):
    message: str

@router.post("/chat")
async def call_agent(input: Input, user: Athlete = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await run_agent(input.message, user.id, db)
    return res

@router.get("/history")
async def get_last_message(user: Athlete = Depends(get_current_user), db: AsyncSession = Depends(get_db)): 
    query = select(Message).where(Message.athlete_id == user.id).order_by(Message.created_at.desc()).limit(1)
    res = await db.execute(query)
    message = res.scalar_one_or_none()

    if not message: 
        return "User has no chat history. Try sending a message first." # this line was flagged

    return message


