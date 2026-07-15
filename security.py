from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta
from os import getenv
from dotenv import load_dotenv
from database import get_db
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Athlete
from cache import redis_client
from types import SimpleNamespace
import jwt , json

load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/signin")

key = getenv("SECRET_KEY")

pwd_context = CryptContext(schemes=["bcrypt"])

def hash_password(pwd: str): 
    print(f"LENGTH: {len(pwd)}, VALUE: {pwd!r}")
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

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> SimpleNamespace : 
    try:
        check = decode_token(token)
    except Exception as e:
        print(f"DECODE ! FAILED: {type(e).__name__}: {e}")
        raise HTTPException(status_code=401, detail="invalid token")
    
    athlete_id = int(check["sub"])
    key = f"id:{athlete_id}"

    cached = await redis_client.get(key) 
    if cached:
        return SimpleNamespace(**json.loads(cached)) # turns json string to python object (a dict)

    else:
        user = await db.execute(
            select(Athlete).where(Athlete.id == athlete_id)
        )

        athlete = user.scalar_one_or_none()
        
        if athlete is None:
            raise HTTPException(status_code=401, detail =  "No athlete found with given id")
        
        athlete_dict = {
            "id": athlete.id,
            "name": athlete.name,
            "email": athlete.email,
            "age": athlete.age,
            "height": athlete.height,
        }
        # add to cache
        await redis_client.set(key, json.dumps(athlete_dict), ex=300) # json.dumps turns a python object into a json string

        return SimpleNamespace(**athlete_dict)