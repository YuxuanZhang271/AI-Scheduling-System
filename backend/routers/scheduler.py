# routers/scheduler.py
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from bson import ObjectId

from database import db
from models import (
    FIXED_TASK_COLLECTION,
    FLEXIBLE_TASK_COLLECTION,
)
from utils.scheduler_updated import Scheduler, DATETIME_FORMAT

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])

def _dt_to_str(dtobj):
    """将 datetime 对象转换为字符串"""
    if isinstance(dtobj, str):
        return dtobj
    return dtobj.strftime(DATETIME_FORMAT)

@router.post("/run/{user_id}")
async def run_scheduler(user_id: str):
    """
    运行智能调度核心流程：
    1. 初始化调度器（读取固定任务、已分配、未分配任务）
    2. 排列任务到时间窗口
    3. 窗口内最优排序
    4. 分配休息时间 -> 计算 start_time
    5. 将分配结果写回 MongoDB
    """
    try:
        print(f"\n{'='*60}")
        print(f"🚀 SCHEDULER START for user: {user_id}")
        print(f"{'='*60}")
        
        # ===== 1) 初始化调度器 =====
        sch = Scheduler(user_id)
        await sch.initScheduler()
        
        print(f"📊 Initial state:")
        print(f"   - Timetable tasks: {len(sch.timetable)}")
        print(f"   - Windows: {len(sch.windows)}")
        print(f"   - Unscheduled tasks: {len(sch.unscheduled_tasks)}")
        
        # ===== 2) 排列任务到窗口 =====
        sch.arrangeTasksToWindows()
        print(f"\n📍 After arranging to windows:")
        print(f"   - Tasks in windows: {sum(len(w['tasks']) for w in sch.windows)}")
        print(f"   - Remaining unscheduled: {len(sch.unscheduled_tasks)}")
        
        # ===== 3) 窗口内排序 =====
        sch.scheduleTasksInWindow()
        print(f"\n⏱️ After scheduling in windows:")
        for i, w in enumerate(sch.windows):
            if w['tasks']:
                print(f"   - Window {i}: {len(w['tasks'])} tasks, score={w.get('score', 'N/A')}")
        
        # ===== 4) 分配休息时间（计算 start_time） =====
        sch.distributeRestTimes()
        print(f"\n😴 After distributing rest times:")
        
        # ===== 5) 更新数据库 =====
        print(f"\n💾 Updating database...")
        updated_count = 0
        failed_count = 0
        
        for w_idx, window in enumerate(sch.windows):
            for task_idx, task in enumerate(window["tasks"]):
                task_id = task.get("task_id")
                start_time = task.get("start_time")
                # ✅ 修复：从任务对象中获取正确的持续时间
                duration = int(task.get("duration", 60))  # 这里应该是分钟数
                
                if not task_id or not start_time:
                    print(f"⚠️  Window {w_idx}, Task {task_idx}: Missing task_id or start_time")
                    failed_count += 1
                    continue
                
                try:
                    # 确保 start_time 是字符串格式
                    if not isinstance(start_time, str):
                        start_time = _dt_to_str(start_time)
                    
                    # ✅ 修复：计算结束时间 - 使用正确的持续时间
                    st_dt = datetime.strptime(start_time, DATETIME_FORMAT)
                    et_dt = st_dt + timedelta(minutes=duration)
                    end_time = et_dt.strftime(DATETIME_FORMAT)
                    
                    print(f"   📝 Updating task {task_id[:8]}... | {start_time} -> {end_time} | duration={duration}min ({duration/60}h)")
                    
                    # 更新数据库
                    result = await db[FLEXIBLE_TASK_COLLECTION].update_one(
                        {"_id": ObjectId(task_id)},
                        {
                            "$set": {
                                "start_time": start_time,
                                "end_time": end_time,
                                "status": "assigned",
                            }
                        },
                    )
                    
                    if result.modified_count > 0:
                        print(f"   ✅ Updated task {task_id[:8]}... successfully")
                        updated_count += 1
                    else:
                        print(f"   ⚠️  Task {task_id[:8]}... not found or not modified")
                        failed_count += 1
                        
                except Exception as e:
                    print(f"   ❌ Failed to update task {task_id[:8]}...: {e}")
                    failed_count += 1
        
        # ===== 6) 返回结果 =====
        print(f"\n{'='*60}")
        print(f"✅ SCHEDULER COMPLETE")
        print(f"   - Successfully updated: {updated_count} tasks")
        print(f"   - Failed: {failed_count} tasks")
        print(f"   - Unscheduled: {len(sch.unscheduled_tasks)} tasks")
        print(f"{'='*60}\n")
        
        return {
            "success": True,
            "message": f"✅ Scheduler completed: {updated_count} tasks assigned",
            "updated_task_ids": [t.get("task_id") for w in sch.windows for t in w["tasks"]],
            "unscheduled_count": len(sch.unscheduled_tasks),
            "unscheduled_tasks": sch.unscheduled_tasks,
        }
        
    except Exception as e:
        print(f"\n❌ SCHEDULER ERROR:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        raise HTTPException(status_code=500, detail=f"Scheduler error: {str(e)}")