import os
from datetime import timedelta, datetime
from jose import jwt

from fastapi import APIRouter, HTTPException

from database import db
from models import USER_COLLECTION
from schemas import UserCreate

router = APIRouter(prefix="/login", tags=["login"])

SECRET_KEY = os.getenv("SECRET_KEY", "Ez61AEU4tKk48k3Au5L8Yy27ze7MI8a5-Qia_X4Dkh0")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict, expires_delta: timedelta = None):
    """生成 JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/")
async def login(request: UserCreate):
    username = request.username
    password = request.password

    if username is None or password is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid username or password"
        )
    result = await db[USER_COLLECTION].find_one({"username": username})
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    elif result["password"] != password:
        raise HTTPException(
            status_code=400,
            detail="Incorrect password"
        )
    else:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": username,
                "user_id": str(result["_id"])
            },
            expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": str(result["_id"])
        }
