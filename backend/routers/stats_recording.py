import datetime as dt
import os

from database import db
from fastapi import APIRouter, Depends, HTTPException, Header
from jose import jwt, JWTError
from models import USER_STATS_COLLECTION
from pydantic import BaseModel
from schemas import UserStats


DATETIME_FORMAT = "%Y%m%d%H%M"
router = APIRouter(prefix="/recording", tags=["recording"])
SECRET_KEY = os.getenv("SECRET_KEY", "Ez61AEU4tKk48k3Au5L8Yy27ze7MI8a5-Qia_X4Dkh0")
ALGORITHM = "HS256"


def get_current_user_id(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token header format")

    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token missing user_id")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Token verification failed")


@router.post("/")
async def record_user_stats(request: UserStats, user_id: str = Depends(get_current_user_id)):
    record = request.dict()
    record.update({
        "user_id": user_id, 
        "datetime": dt.datetime.now().strftime(DATETIME_FORMAT)
    })

    collection = db[USER_STATS_COLLECTION]
    if not collection:
        raise HTTPException(status_code=500, detail="Database collection not found")

    try:
        result = await collection.insert_one(record)
        return {"status": "success", "inserted_id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database insertion error: {e}")