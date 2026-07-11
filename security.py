from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta
from os import getenv
from database import get_db
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Athlete
import jwt  

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

key = getenv("SECRET_KEY")

pwd_context = CryptContext(schemes=["bcrypt"])

def hash_password(pwd: str): 
    return pwd_context.hash(pwd)

def verify(plain_pwd: str, hashed: str) -> bool:
    return pwd_context.verify(plain_pwd, hashed)

def create_token(data: dict) -> str:
    to_encode = data.copy() # don't want to mutate the data that's passed
    exp = datetime.now(timezone.utc) + timedelta(minutes = 30)
    to_encode.update({"exp": exp})
    return jwt.encode( to_encode, key, algorithm="HS256")

def decode_token(token: str) -> dict:
    return jwt.decode(token, key, algorithms=["HS256"])

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> Athlete: 
    try:
        check = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="invalid token")
    athlete_id = check["sub"]
    user = await db.execute(
        select(Athlete).where(Athlete.id == athlete_id)
    )

    athlete = user.scalar_one_or_none()
    if athlete is None:
        raise HTTPException(status_code=401, detail =  "No athlete found with given id")
    
    return athlete
