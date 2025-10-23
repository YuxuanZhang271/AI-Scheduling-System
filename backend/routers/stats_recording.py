# ==================== stats_recording.py ====================
import datetime as dt
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List
from database import db
from models import FIXED_TASK_COLLECTION, FLEXIBLE_TASK_COLLECTION
from bson import ObjectId

router = APIRouter(prefix="/stats", tags=["Statistics & Recording"])
DATETIME_FORMAT = "%Y%m%d%H%M"

# ✅ 恢复率配置（基于任务类型）
RECOVERY_RATES = {
    "food": {
        "energy_per_hour": 0.8,      # 吃饭后每小时恢复 0.8 能量
        "pressure_per_hour": -0.5    # 吃饭后每小时降低 0.5 压力
    },
    "fun": {
        "energy_per_hour": 0.6,      # 娱乐后恢复较慢
        "pressure_per_hour": -0.8    # 但压力降低很快
    },
    "work": {
        "energy_per_hour": 0.4,      # 工作后恢复慢
        "pressure_per_hour": -0.2    # 压力降低也慢
    },
    "default": {
        "energy_per_hour": 0.5,      # 默认恢复率
        "pressure_per_hour": -0.3
    }
}


def normalize_time(value):
    """统一时间字段转字符串 YYYYMMDDHHMM"""
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


def calculate_energy_pressure_timeline(tasks: list, start_hour: int = 8, end_hour: int = 20):
    """
    根据任务列表计算一天中每个时间点的能量和压力
    
    核心逻辑：
    1. 初始状态（8:00）：能量=5.0, 压力=0.0
    2. 任务执行：
       - 能量消耗 = predicted_energy（模型预测的 energy_loss）
       - 压力增加 = predicted_pressure（模型预测的 pressure_increase）
    3. 休息恢复：
       - 根据上一个任务的类型，应用不同的恢复率
       - 能量恢复 = energy_per_hour × 休息小时数
       - 压力降低 = pressure_per_hour × 休息小时数
    
    Args:
        tasks: 任务列表，需包含：
            - start_time (str): "YYYYMMDDHHMM"
            - duration (int): 分钟数
            - predicted_energy (float): AI 预测的能量消耗
            - predicted_pressure (float): AI 预测的压力增加
            - task_type (str): "food"/"fun"/"work"
        start_hour: 开始时间（默认 8:00）
        end_hour: 结束时间（默认 20:00）
        
    Returns:
        {
            "energy_data": [{"time": "08:00", "value": 5.0}, ...],
            "pressure_data": [{"time": "08:00", "value": 0.0}, ...]
        }
    """
    # 初始化：早上满能量，无压力
    current_energy = 5.0
    current_pressure = 0.0
    
    energy_timeline = []
    pressure_timeline = []
    
    # 按开始时间排序任务
    sorted_tasks = sorted(
        [t for t in tasks if t.get("start_time")],
        key=lambda x: normalize_time(x.get("start_time"))
    )
    
    # 记录上一个任务的结束时间和类型（用于计算休息恢复）
    last_task_end_hour = start_hour
    last_task_type = "default"
    
    # 生成时间轴（每2小时一个点）
    timeline_hours = list(range(start_hour, end_hour + 1, 2))
    
    for hour in timeline_hours:
        time_str = f"{hour:02d}:00"
        
        # 查找在这个时间点之前完成的所有任务
        for task in sorted_tasks:
            if task.get("_processed", False):
                continue  # 跳过已处理的任务
                
            try:
                start_time_str = normalize_time(task.get("start_time"))
                if len(start_time_str) < 12:
                    continue
                
                # 解析任务时间
                task_start_hour = int(start_time_str[8:10])
                task_start_minute = int(start_time_str[10:12])
                
                # 获取持续时间（分钟）
                duration = task.get("duration", 60)
                if duration < 10:  # 如果小于10，认为是小时
                    duration = duration * 60
                
                # 计算任务结束时间
                task_end_hour = task_start_hour + ((task_start_minute + duration) // 60)
                
                # 如果任务在当前时间点之前结束
                if task_end_hour <= hour:
                    # 1. 应用上一个任务后的休息恢复
                    rest_hours = task_start_hour - last_task_end_hour
                    if rest_hours > 0:
                        recovery_rate = RECOVERY_RATES.get(last_task_type, RECOVERY_RATES["default"])
                        current_energy = min(5.0, current_energy + rest_hours * recovery_rate["energy_per_hour"])
                        current_pressure = max(0.0, current_pressure + rest_hours * recovery_rate["pressure_per_hour"])
                    
                    # 2. 应用任务的影响（使用 AI 模型预测值）
                    energy_loss = abs(task.get("predicted_energy", 1.0))  # 取绝对值，确保是消耗
                    pressure_gain = abs(task.get("predicted_pressure", 0.5))  # 取绝对值，确保是增加
                    
                    current_energy = max(0.0, current_energy - energy_loss)
                    current_pressure = min(5.0, current_pressure + pressure_gain)
                    
                    # 3. 更新状态
                    task["_processed"] = True
                    last_task_end_hour = task_end_hour
                    last_task_type = task.get("task_type", "default")
                    
            except Exception as e:
                print(f"    ⚠️ Error processing task: {e}")
                continue
        
        # 如果当前时间点距离上一个任务结束有间隔，继续恢复
        rest_hours = hour - last_task_end_hour
        if rest_hours > 0:
            recovery_rate = RECOVERY_RATES.get(last_task_type, RECOVERY_RATES["default"])
            current_energy = min(5.0, current_energy + rest_hours * recovery_rate["energy_per_hour"])
            current_pressure = max(0.0, current_pressure + rest_hours * recovery_rate["pressure_per_hour"])
            last_task_end_hour = hour
        
        # 记录当前时间点的状态
        energy_timeline.append({"time": time_str, "value": round(current_energy, 2)})
        pressure_timeline.append({"time": time_str, "value": round(current_pressure, 2)})
    
    return {
        "energy_data": energy_timeline,
        "pressure_data": pressure_timeline
    }


@router.get("/daily")
async def get_daily_stats(date: str = Query(...), user_id: str = Query(...)):
    """
    返回指定日期的任务统计
    
    ✅ 使用 AI 模型预测值 + 基于任务类型的恢复率
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
        
        # 统一任务格式（fixed 和 flexible 的字段名不同）
        normalized_tasks = []
        for t in todays_fixed:
            normalized_tasks.append({
                "start_time": t.get("task_start_time"),
                "duration": t.get("task_duration", 60),
                "task_type": t.get("task_type", "work"),
                "predicted_energy": t.get("predicted_energy", 1.0),
                "predicted_pressure": t.get("predicted_pressure", 0.5),
                "status": t.get("status")
            })
        
        for t in todays_flex:
            normalized_tasks.append({
                "start_time": t.get("start_time"),
                "duration": t.get("expected_duration", 60),
                "task_type": t.get("task_type", "work"),
                "predicted_energy": t.get("predicted_energy", 1.0),
                "predicted_pressure": t.get("predicted_pressure", 0.5),
                "status": t.get("status")
            })
        
        print(f"  Normalized {len(normalized_tasks)} tasks for timeline calculation")
        
        # 统计数据
        total_tasks = len(normalized_tasks)
        completed_tasks = sum(1 for t in normalized_tasks if t.get("status") == "completed")
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
        
        # 类型分布
        tasks_by_type: Dict[str, int] = {}
        for t in normalized_tasks:
            task_type = t.get("task_type", "unknown")
            tasks_by_type[task_type] = tasks_by_type.get(task_type, 0) + 1
        
        # ✅ 使用 AI 模型预测值计算能量和压力时间轴
        timeline = calculate_energy_pressure_timeline(normalized_tasks)
        
        result = {
            "tasks_by_type": tasks_by_type,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": round(completion_rate, 1),
            "energy_data": timeline["energy_data"],
            "pressure_data": timeline["pressure_data"],
        }
        
        print(f"  ✅ Daily stats: {total_tasks} tasks, {len(timeline['energy_data'])} timeline points")
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
    """返回指定周的任务统计"""
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
        
        avg_energy_data = []
        avg_pressure_data = []
        
        DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
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
            
            # 统一格式
            day_normalized = []
            for t in day_fixed:
                day_normalized.append({
                    "start_time": t.get("task_start_time"),
                    "duration": t.get("task_duration", 60),
                    "task_type": t.get("task_type", "work"),
                    "predicted_energy": t.get("predicted_energy", 1.0),
                    "predicted_pressure": t.get("predicted_pressure", 0.5),
                    "status": t.get("status")
                })
            
            for t in day_flex:
                day_normalized.append({
                    "start_time": t.get("start_time"),
                    "duration": t.get("expected_duration", 60),
                    "task_type": t.get("task_type", "work"),
                    "predicted_energy": t.get("predicted_energy", 1.0),
                    "predicted_pressure": t.get("predicted_pressure", 0.5),
                    "status": t.get("status")
                })
            
            # 统计
            day_total = len(day_normalized)
            day_completed = sum(1 for t in day_normalized if t.get("status") == "completed")
            
            daily_stats.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "total_tasks": day_total,
                "completed_tasks": day_completed,
            })
            
            # 累加周统计
            total_tasks += day_total
            completed_tasks += day_completed
            
            # 累加类型统计
            for t in day_normalized:
                task_type = t.get("task_type", "unknown")
                tasks_by_type[task_type] = tasks_by_type.get(task_type, 0) + 1
            
            # ✅ 计算当天的平均能量和压力
            if day_normalized:
                timeline = calculate_energy_pressure_timeline(day_normalized)
                avg_energy = sum(p["value"] for p in timeline["energy_data"]) / len(timeline["energy_data"])
                avg_pressure = sum(p["value"] for p in timeline["pressure_data"]) / len(timeline["pressure_data"])
            else:
                avg_energy = 5.0
                avg_pressure = 0.0
            
            day_name = DAY_NAMES[current_date.weekday()]
            avg_energy_data.append({"day": day_name, "value": round(avg_energy, 2)})
            avg_pressure_data.append({"day": day_name, "value": round(avg_pressure, 2)})
            
            current_date += dt.timedelta(days=1)
        
        # 完成率
        completion_rate = (completed_tasks / total_tasks) if total_tasks > 0 else 0.0
        
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
