# stats_recording.py
import datetime as dt
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional
from database import db
from models import FIXED_TASK_COLLECTION, FLEXIBLE_TASK_COLLECTION
from bson import ObjectId

router = APIRouter(prefix="/stats", tags=["Statistics & Recording"])
DATETIME_FORMAT = "%Y%m%d%H%M"

def _is_same_day(yyyymmddhhmm: str, yyyymmdd: str) -> bool:
    return isinstance(yyyymmddhhmm, str) and len(yyyymmddhhmm) >= 8 and yyyymmddhhmm[:8] == yyyymmdd


def normalize_time(value):
    """统一时间字段转字符串"""
    if isinstance(value, dt.datetime):
        return value.strftime("%Y%m%d%H%M")
    elif isinstance(value, (int, float)):
        return str(int(value))
    return str(value or "")


def make_user_query(user_id: str):
    """构建用户查询条件"""
    try:
        obj_id = ObjectId(user_id)
        return {"$or": [
            {"_id": obj_id},
            {"user_id": str(user_id)},
            {"user_id": user_id}
        ]}
    except Exception:
        return {"$or": [
            {"user_id": str(user_id)},
            {"user_id": user_id}
        ]}


@router.get("/daily")
async def get_daily_stats(date: str = Query(...), user_id: str = Query(...)):
    """
    返回指定日期的任务统计
    
    Args:
        date: 日期字符串 "YYYY-MM-DD"
        user_id: 用户ID
        
    Returns:
        {
            "tasks_by_type": {"work": 5, "fun": 2},
            "total_tasks": 7,
            "completed_tasks": 5,
            "completion_rate": 71.4,
            "energy_data": [...],
            "pressure_data": [...]
        }
    """
    try:
        print(f"\n📊 GET /stats/daily - date={date}, user_id={user_id}")
        
        # 解析日期
        try:
            date_obj = dt.datetime.strptime(date, "%Y-%m-%d")
            day_key = date_obj.strftime("%Y%m%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # 构建查询
        base_query = make_user_query(user_id)
        
        # 获取任务
        fixed_tasks = await db[FIXED_TASK_COLLECTION].find(base_query).to_list(None)
        flex_tasks = await db[FLEXIBLE_TASK_COLLECTION].find(base_query).to_list(None)
        
        print(f"  Found {len(fixed_tasks)} fixed tasks, {len(flex_tasks)} flexible tasks")
        
        # 筛选当天的任务
        def is_on_date(task, is_fixed=False):
            if is_fixed:
                start_time = normalize_time(task.get("task_start_time"))
                end_time = normalize_time(task.get("task_end_time"))
                return (start_time[:8] == day_key) or (end_time[:8] == day_key)
            else:
                start_time = normalize_time(task.get("start_time"))
                return start_time[:8] == day_key
        
        todays_fixed = [t for t in fixed_tasks if is_on_date(t, is_fixed=True)]
        todays_flex = [t for t in flex_tasks if is_on_date(t, is_fixed=False)]
        todays_all = todays_fixed + todays_flex
        
        print(f"  Filtered to {len(todays_all)} tasks on {day_key}")
        
        # 统计数据
        total_tasks = len(todays_all)
        completed_tasks = sum(1 for t in todays_all if t.get("status") == "completed")
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
        
        # 类型分布
        tasks_by_type: Dict[str, int] = {}
        for t in todays_all:
            task_type = t.get("task_type", "unknown")
            tasks_by_type[task_type] = tasks_by_type.get(task_type, 0) + 1
        
        # 能量和压力数据（模拟数据，你可以从实际记录中获取）
        energy_data = []
        pressure_data = []
        
        # 如果有任务，生成一些示例数据点
        if todays_all:
            for hour in range(8, 20, 2):  # 8:00 到 20:00，每2小时一个点
                time_str = f"{hour:02d}:00"
                
                # 计算该时段的平均预测值
                hour_tasks = [
                    t for t in todays_all 
                    if normalize_time(t.get("start_time" if "start_time" in t else "task_start_time"))[8:10] == f"{hour:02d}"
                ]
                
                if hour_tasks:
                    avg_energy = sum(t.get("predicted_energy", 1.0) for t in hour_tasks) / len(hour_tasks)
                    avg_pressure = sum(t.get("predicted_pressure", 0.5) for t in hour_tasks) / len(hour_tasks)
                else:
                    avg_energy = 1.0
                    avg_pressure = 0.5
                
                energy_data.append({"time": time_str, "value": round(avg_energy, 2)})
                pressure_data.append({"time": time_str, "value": round(avg_pressure, 2)})
        
        result = {
            "tasks_by_type": tasks_by_type,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": round(completion_rate, 1),
            "energy_data": energy_data,
            "pressure_data": pressure_data,
        }
        
        print(f"  ✅ Daily stats: {result}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Daily stats error: {str(e)}")


@router.get("/weekly")
async def get_weekly_stats(
    start_date: str = Query(...),
    end_date: str = Query(...),
    user_id: str = Query(...)
):
    """
    返回指定周的任务统计
    
    Args:
        start_date: 开始日期 "YYYY-MM-DD"
        end_date: 结束日期 "YYYY-MM-DD"
        user_id: 用户ID
        
    Returns:
        {
            "daily_stats": [...],
            "tasks_by_type": {"work": 20, "fun": 10},
            "total_tasks": 30,
            "completed_tasks": 25,
            "completion_rate": 0.833,
            "avg_energy_data": [...],
            "avg_pressure_data": [...]
        }
    """
    try:
        print(f"\n📊 GET /stats/weekly - start={start_date}, end={end_date}, user_id={user_id}")
        
        # 解析日期
        try:
            start_dt = dt.datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = dt.datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # 构建查询
        base_query = make_user_query(user_id)
        
        # 获取所有任务
        fixed_tasks = await db[FIXED_TASK_COLLECTION].find(base_query).to_list(None)
        flex_tasks = await db[FLEXIBLE_TASK_COLLECTION].find(base_query).to_list(None)
        
        print(f"  Found {len(fixed_tasks)} fixed tasks, {len(flex_tasks)} flexible tasks")
        
        # 按日期分组统计
        daily_stats = []
        total_tasks = 0
        completed_tasks = 0
        tasks_by_type: Dict[str, int] = {}
        
        current_date = start_dt
        while current_date <= end_dt:
            day_key = current_date.strftime("%Y%m%d")
            
            # 筛选当天的任务
            def is_on_date(task, is_fixed=False):
                if is_fixed:
                    start_time = normalize_time(task.get("task_start_time"))
                    end_time = normalize_time(task.get("task_end_time"))
                    return (start_time[:8] == day_key) or (end_time[:8] == day_key)
                else:
                    start_time = normalize_time(task.get("start_time"))
                    return start_time[:8] == day_key
            
            day_fixed = [t for t in fixed_tasks if is_on_date(t, is_fixed=True)]
            day_flex = [t for t in flex_tasks if is_on_date(t, is_fixed=False)]
            day_all = day_fixed + day_flex
            
            # 统计
            day_total = len(day_all)
            day_completed = sum(1 for t in day_all if t.get("status") == "completed")
            
            daily_stats.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "total_tasks": day_total,
                "completed_tasks": day_completed,
            })
            
            # 累加周统计
            total_tasks += day_total
            completed_tasks += day_completed
            
            # 累加类型统计
            for t in day_all:
                task_type = t.get("task_type", "unknown")
                tasks_by_type[task_type] = tasks_by_type.get(task_type, 0) + 1
            
            current_date += dt.timedelta(days=1)
        
        # 完成率
        completion_rate = (completed_tasks / total_tasks) if total_tasks > 0 else 0.0
        
        # 能量和压力数据（每天的平均值）
        DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        avg_energy_data = []
        avg_pressure_data = []
        
        for stat in daily_stats:
            date_obj = dt.datetime.strptime(stat["date"], "%Y-%m-%d")
            day_name = DAY_NAMES[date_obj.weekday()]
            
            # 这里使用随机值，你可以从实际数据中计算
            avg_energy_data.append({"day": day_name, "value": 3.5})
            avg_pressure_data.append({"day": day_name, "value": 2.5})
        
        result = {
            "daily_stats": daily_stats,
            "tasks_by_type": tasks_by_type,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": round(completion_rate, 3),
            "avg_energy_data": avg_energy_data,
            "avg_pressure_data": avg_pressure_data,
        }
        
        print(f"  ✅ Weekly stats: total={total_tasks}, completed={completed_tasks}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Weekly stats error: {str(e)}")


@router.post("/record")
async def record_user_condition(
    user_id: str = Query(...),
    timestamp: str = Query(...),
    energy: float = Query(...),
    pressure: float = Query(...)
):
    """
    记录用户的能量和压力状态
    
    Args:
        user_id: 用户ID
        timestamp: 时间戳 "YYYYMMDDHHMM"
        energy: 能量值 (0-5)
        pressure: 压力值 (0-5)
    """
    try:
        print(f"\n📝 POST /stats/record - user={user_id}, time={timestamp}, energy={energy}, pressure={pressure}")
        
        # 创建记录文档
        record = {
            "user_id": user_id,
            "timestamp": timestamp,
            "energy": energy,
            "pressure": pressure,
            "created_at": dt.datetime.now()
        }
        
        # 存储到 conditions 集合
        result = await db["user_conditions"].insert_one(record)
        
        print(f"  ✅ Condition recorded with ID: {result.inserted_id}")
        
        return {
            "success": True,
            "record_id": str(result.inserted_id),
            "message": "Condition recorded successfully"
        }
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        raise HTTPException(status_code=500, detail=f"Record error: {str(e)}")
