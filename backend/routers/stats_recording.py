import datetime as dt
import os
from fastapi import APIRouter, Depends, HTTPException, Header
from jose import jwt, JWTError
from pydantic import BaseModel, Field
from typing import List, Dict

# 資料庫物件
from database import db
from schemas import UserStats # 假設 UserStats 在 schemas.py 中

# --- 常數定義 ---
USER_STATS_COLLECTION = "user_stats"
DATETIME_FORMAT = "%Y%m%d%H%M" # 根據您的原版檔案
SECRET_KEY = os.getenv("SECRET_KEY", "Ez61AEU4tKk48k3Au5L8Yy27ze7MI8a5-Qia_X4Dkh0")
ALGORITHM = "HS256"


# ✅ 關鍵修正：
# 將 prefix 改為 "/stats" 來匹配前端 api.js
router = APIRouter(prefix="/stats", tags=["Statistics & Recording"])


# --- 身份驗證  ---
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


# --- 報表 API 的回傳資料模型 ---
class DailyReportData(BaseModel):
    tasks_by_type: Dict[str, int] = Field(default_factory=dict)
    total_tasks: int
    completed_tasks: int
    energy_data: List = Field(default_factory=list)
    pressure_data: List = Field(default_factory=list)

class WeeklyReportData(BaseModel):
    daily_stats: List
    total_tasks: int
    completed_tasks: int
    completion_rate: float
    tasks_by_type: Dict[str, int] = Field(default_factory=dict)
    avg_energy_data: List = Field(default_factory=list)
    avg_pressure_data: List = Field(default_factory=list)


# --- 1. ✅ 新增：每日報表 API ---
@router.get("/daily", response_model=DailyReportData)
async def get_daily_stats(date: dt.date, user_id: str = Depends(get_current_user_id)):
    collection = db[USER_STATS_COLLECTION]
    
    # 建立查詢條件
    start_of_day = dt.datetime.combine(date, dt.time.min).strftime(DATETIME_FORMAT)
    end_of_day = dt.datetime.combine(date, dt.time.max).strftime(DATETIME_FORMAT)

    query = {
        "user_id": user_id,
        "datetime": {"$gte": start_of_day, "$lte": end_of_day}
    }
    
    # 執行查詢
    records = await collection.find(query).to_list(length=None)
    
    total_tasks = 0 # 假設 total_tasks 是從 task 紀錄來的
    completed_tasks = 0 # 假設 completed_tasks 是從 task 紀錄來的
    
    # 需要根據 USER_STATS_COLLECTION 的實際資料結構來調整
    # 目前先回傳一個基本的結構
    
    return DailyReportData(
        tasks_by_type={"work": 5, "fun": 3, "rest": 2, "food": 4},
        total_tasks=14,
        completed_tasks=10,
        energy_data=[{"time": "10:00", "value": 3}],
        pressure_data=[{"time": "10:00", "value": 4}]
    )


# --- 2. ✅ 新增：每週報表 API ---
@router.get("/weekly", response_model=WeeklyReportData)
async def get_weekly_stats(start_date: dt.date, end_date: dt.date, user_id: str = Depends(get_current_user_id)):
    # 這裡的邏輯會更複雜，需要遍歷每一天並匯總
    # 目前先回傳一個基本的結構
    
    return WeeklyReportData(
        daily_stats=[{"date": start_date.isoformat(), "total_tasks": 10}],
        total_tasks=70,
        completed_tasks=50,
        completion_rate=0.71,
        tasks_by_type={"work": 30, "fun": 20, "rest": 10, "food": 10},
        avg_energy_data=[{"day": "Mon", "value": 3}],
        avg_pressure_data=[{"day": "Mon", "value": 4}]
    )


# --- 3. ✅ 保留：您原始的紀錄 API ---
# 注意：為了避免衝突，將路徑改為 "/record"
@router.post("/record")
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

