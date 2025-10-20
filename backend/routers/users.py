from fastapi import APIRouter, HTTPException
from bson import ObjectId
from database import db
from models import USER_COLLECTION
from schemas import UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserOut)
async def create_user(user: UserCreate):
    new_user = user.dict()
    result = await db[USER_COLLECTION].insert_one(new_user)
    return UserOut(id=str(result.inserted_id), **new_user)


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: str):
    user = await db[USER_COLLECTION].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user["id"] = str(user["_id"])
    return UserOut(**user)