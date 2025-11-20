from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from bson import ObjectId
from database import db
from models import FIXED_TASK_COLLECTION, FLEXIBLE_TASK_COLLECTION, USER_COLLECTION

router = APIRouter(prefix="/tasks", tags=["Tasks"])

DATETIME_FORMAT = "%Y%m%d%H%M"  # ✅ 先定义格式

# 获取本地时间而不是 UTC
now = datetime.now()
print(f"🕐 System time: {now.strftime(DATETIME_FORMAT)}")
print(f"🕐 UTC time: {datetime.utcnow().strftime(DATETIME_FORMAT)}")


def make_user_query(user_id: str):
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


@router.get("/{user_id}")
async def get_tasks(user_id: str, show_all: bool = True):  # ✅ 改为默认显示所有任务
    """
    获取某个用户的所有任务，自动更新状态
    ✅ show_all=True: 显示所有任务（用于dashboard）
    ✅ show_all=False: 只显示当天任务（用于主界面）
    """
    try:
        query = make_user_query(user_id)
        now = datetime.now()
        today_str = now.strftime("%Y%m%d")  # 获取今天的日期字符串
        print(f"\n🕐 Current time: {now.strftime(DATETIME_FORMAT)}")
        print(f"📅 Today's date: {today_str}")
        print(f"🔍 Show all tasks: {show_all}")

        # 获取 fixed & flexible
        fixed_tasks = await db[FIXED_TASK_COLLECTION].find(query).to_list(None)
        flex_tasks = await db[FLEXIBLE_TASK_COLLECTION].find(query).to_list(None)

        # 用于存储要返回的任务列表
        filtered_fixed_tasks = []
        filtered_flex_tasks = []

        # ✅ 自动更新 fixed 任务状态 - 检查是否超过结束时间
        print(f"📋 Checking {len(fixed_tasks)} fixed tasks:")
        for t in fixed_tasks:
            task_name = t.get('task_name', 'N/A')
            end_time_str = t.get("task_end_time")
            current_status = t.get("status", "assigned")
            
            # ✅ 如果没有 end_time，从 start_time 和 duration 动态计算
            if not end_time_str and t.get("task_start_time") and t.get("task_duration"):
                try:
                    start_dt = datetime.strptime(t.get("task_start_time"), DATETIME_FORMAT)
                    duration = int(t.get("task_duration", 0))
                    end_dt = start_dt + timedelta(minutes=duration)
                    end_time_str = end_dt.strftime(DATETIME_FORMAT)
                    
                    # 保存到数据库，以便下次不需要重新计算
                    await db[FIXED_TASK_COLLECTION].update_one(
                        {"_id": t["_id"]},
                        {"$set": {"task_end_time": end_time_str}}
                    )
                    print(f"  ✅ Calculated end_time for {task_name}: {end_time_str}")
                except Exception as e:
                    print(f"  ⚠️ Error calculating end_time for {task_name}: {e}")
                    continue
            
            print(f"  - {task_name}: status={current_status}, end_time={end_time_str}")
            
            if end_time_str and isinstance(end_time_str, str):
                try:
                    end_dt = datetime.strptime(end_time_str, DATETIME_FORMAT)
                    print(f"    Parsed end_time: {end_dt}")
                    print(f"    Now: {now}")
                    print(f"    Now >= end_dt? {now >= end_dt}")
                    
                    new_status = "completed" if now >= end_dt else "assigned"
                    
                    if current_status != new_status:
                        await db[FIXED_TASK_COLLECTION].update_one(
                            {"_id": t["_id"]},
                            {"$set": {"status": new_status}}
                        )
                        t["status"] = new_status
                        print(f"    ✅ Updated to {new_status}")
                    else:
                        print(f"    Status unchanged: {current_status}")
                except Exception as e:
                    print(f"    ❌ Error: {e}")

            # ✅ 检查是否是当天的任务（只有在 show_all=false 时才过滤）
            if not show_all:  # 只显示当天任务
                task_date_str = None
                # 尝试从不同字段获取任务日期
                for time_field in ["task_start_time", "task_end_time", "start_time"]:
                    time_str = t.get(time_field)
                    if time_str and isinstance(time_str, str) and len(time_str) >= 8:
                        task_date_str = time_str[:8]  # 提取 YYYYMMDD
                        break
                
                if task_date_str == today_str:
                    filtered_fixed_tasks.append(t)
                    print(f"    📌 Included in today's view (date: {task_date_str})")
                else:
                    print(f"    ⏳ Excluded from today's view (date: {task_date_str}, today: {today_str})")
            else:
                # show_all=true，包含所有任务
                filtered_fixed_tasks.append(t)

        # ✅ 自动更新 flexible 任务状态
        print(f"📋 Checking {len(flex_tasks)} flexible tasks:")
        for t in flex_tasks:
            task_name = t.get('task_name', 'N/A')
            start_time = t.get("start_time")
            current_status = t.get("status", "unassigned")
            duration = t.get("expected_duration", 60)  # 默认60分钟
            
            print(f"  - {task_name}: status={current_status}, start_time={start_time}, duration={duration}")
            
            if start_time and isinstance(start_time, str):
                try:
                    st_dt = datetime.strptime(start_time, DATETIME_FORMAT)
                    
                    # 计算任务应该结束的时间
                    # 假设 duration 是以分钟为单位
                    end_dt = st_dt + timedelta(minutes=duration)
                    
                    # 状态转换逻辑
                    if current_status == "assigned" and now >= st_dt:
                        # 到达开始时间，变为 processing
                        new_status = "processing"
                        await db[FLEXIBLE_TASK_COLLECTION].update_one(
                            {"_id": t["_id"]},
                            {"$set": {"status": new_status}}
                        )
                        t["status"] = new_status
                        print(f"    ✅ Updated from assigned to processing")
                    
                    elif current_status == "processing" and now >= end_dt:
                        # 超过结束时间，变为 completed
                        new_status = "completed"
                        await db[FLEXIBLE_TASK_COLLECTION].update_one(
                            {"_id": t["_id"]},
                            {"$set": {"status": new_status}}
                        )
                        t["status"] = new_status
                        print(f"    ✅ Updated from processing to completed (ended at {end_dt})")
                    
                    else:
                        print(f"    Status unchanged: {current_status}")
                        
                except Exception as e:
                    print(f"    ❌ Error: {e}")

            # ✅ 检查是否是当天的任务（只有在 show_all=false 时才过滤）
            if not show_all:  # 只显示当天任务
                task_date_str = None
                # 尝试从不同字段获取任务日期
                for time_field in ["start_time", "task_deadline"]:
                    time_str = t.get(time_field)
                    if time_str and isinstance(time_str, str) and len(time_str) >= 8:
                        task_date_str = time_str[:8]  # 提取 YYYYMMDD
                        break
                
                if task_date_str == today_str:
                    filtered_flex_tasks.append(t)
                    print(f"    📌 Included in today's view (date: {task_date_str})")
                else:
                    print(f"    ⏳ Excluded from today's view (date: {task_date_str}, today: {today_str})")
            else:
                # show_all=true，包含所有任务
                filtered_flex_tasks.append(t)

        # --- 转换 ObjectId 为字符串 ---
        for t in filtered_fixed_tasks + filtered_flex_tasks:
            t["_id"] = str(t["_id"])
            t["id"] = t["_id"]

        print(f"\n📥 GET /tasks/{user_id} complete")
        print(f"📊 Returned tasks: {len(filtered_fixed_tasks)} fixed, {len(filtered_flex_tasks)} flexible")
        print(f"📊 All tasks in DB: {len(fixed_tasks)} fixed, {len(flex_tasks)} flexible")
        
        for t in filtered_fixed_tasks + filtered_flex_tasks:
            if "predicted_energy" not in t:
                t["predicted_energy"] = None
            if "predicted_pressure" not in t:
                t["predicted_pressure"] = None

        return {
            "fixed": filtered_fixed_tasks,
            "flexible": filtered_flex_tasks,
            "ai_predictions": True,
            "is_today_view": not show_all,  # 返回当前视图类型
            "today_date": today_str,
            "total_tasks_count": len(filtered_fixed_tasks) + len(filtered_flex_tasks)
        }
    except Exception as e:
        print(f"❌ Error loading tasks: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}")
async def create_task(user_id: str, task: dict):
    """
    创建任务，支持 fixed / flexible 两种模式
    ✅ fixed 任务自动计算结束时间并设置初始状态
    """
    mode = task.get("mode")
    if mode not in ["fixed", "flexible"]:
        raise HTTPException(status_code=400, detail="Invalid task mode")

    try:
        query = make_user_query(user_id)
        user_doc = await db[USER_COLLECTION].find_one(query)
    except Exception as e:
        print("❌ Error finding user:", e)
        raise HTTPException(status_code=500, detail="Database error")

    if user_doc is None:
        print("❌ User not found in MongoDB:", user_id)
        raise HTTPException(status_code=404, detail="User does not exist")

    try:
        if mode == "fixed":
            # 获取开始时间和持续时间
            start_time_str = task.get("startTime", datetime.now().strftime(DATETIME_FORMAT))  # ✅ 改为 now()
            duration_minutes = int(float(task.get("duration", 60)))
            
            # 计算结束时间
            start_dt = datetime.strptime(start_time_str, DATETIME_FORMAT)
            end_dt = start_dt + timedelta(minutes=duration_minutes)
            end_time_str = end_dt.strftime(DATETIME_FORMAT)
            
            # 初始状态：如果当前时间已过结束时间，则设为 completed，否则为 assigned
            now = datetime.now()  # ✅ 改为本地时间
            initial_status = "completed" if now >= end_dt else "assigned"
            
            new_task_doc = {
                "user_id": str(user_id),
                "task_name": task.get("name", ""),
                "task_type": task.get("category", "work"),
                "task_start_time": start_time_str,
                "task_end_time": end_time_str,
                "task_duration": float(task.get("duration", 1)),
                "expected_difficulty": int(task.get("difficulty", 3)),
                "task_location": task.get("location", ""),
                "status": initial_status,
                "created_at": datetime.now(),  # ✅ 改为本地时间
            }

            result = await db[FIXED_TASK_COLLECTION].insert_one(new_task_doc)
            task_id = str(result.inserted_id)

            print(f"✅ Created fixed task {task_id}: {task.get('name')} | {start_time_str} - {end_time_str}")
            
            return {
                "task_id": task_id,
                "message": "✅ Fixed task created successfully",
                "status": initial_status,
            }

        elif mode == "flexible":
            # 确保 deadline 格式为 YYYYMMDDHHMM
            deadline = task.get("deadline", "")
            if "-" in deadline or "T" in deadline:
                dt = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
                deadline = dt.strftime("%Y%m%d%H%M")

            new_task_doc = {
                "user_id": str(user_id),
                "task_name": task.get("name", ""),
                "task_type": task.get("category", "work"),
                "task_deadline": deadline,
                "expected_duration": float(task.get("duration", 60)),
                "expected_difficulty": int(task.get("difficulty", 3)),
                "task_priority": int(task.get("priority", 1)),
                "task_location": task.get("location", ""),
                "status": "unassigned",
                "start_time": None,
                "end_time": None,
                "created_at": datetime.now(),  # ✅ 改为本地时间
            }

            result = await db[FLEXIBLE_TASK_COLLECTION].insert_one(new_task_doc)
            task_id = str(result.inserted_id)

            print(f"✅ Created flexible task {task_id}: {task.get('name')} | deadline={deadline}")
            
            return {
                "task_id": task_id,
                "message": "✅ Flexible task created successfully"
            }

    except Exception as e:
        print("❌ Error creating task:", e)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{task_id}")
async def delete_task(task_id: str, task_type: str = None):
    """
    删除固定任务或灵活任务
    """
    if task_type not in ["fixed", "flex"]:
        raise HTTPException(status_code=400, detail="task_type is required")

    if not task_id or task_id == "undefined":
        raise HTTPException(status_code=400, detail="Invalid task_id")

    try:
        collection = FIXED_TASK_COLLECTION if task_type == "fixed" else FLEXIBLE_TASK_COLLECTION
        result = await db[collection].delete_one({"_id": ObjectId(task_id)})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Task not found")

        print(f"🗑️ Deleted {task_type} task {task_id}")
        return {"task_id": task_id, "message": "Task deleted successfully"}

    except Exception as e:
        print(f"❌ Error deleting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/assign/{task_id}")
async def update_task_status(task_id: str, status: str):
    """
    更新任务状态（flexible 任务）
    """
    try:
        result = await db[FLEXIBLE_TASK_COLLECTION].update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {"status": status}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        
        print(f"✅ Updated task {task_id} status to {status}")
        return {"task_id": task_id, "status": status}
    except Exception as e:
        print(f"❌ Error updating task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    # 在 tasks.py 中添加调试端点
@router.get("/debug/{user_id}")
async def debug_tasks(user_id: str):
    """调试端点：检查任务数据"""
    try:
        query = make_user_query(user_id)
        
        fixed_tasks = await db[FIXED_TASK_COLLECTION].find(query).to_list(None)
        flex_tasks = await db[FLEXIBLE_TASK_COLLECTION].find(query).to_list(None)
        
        print(f"🔍 DEBUG: Found {len(fixed_tasks)} fixed tasks, {len(flex_tasks)} flexible tasks")
        
        for i, task in enumerate(fixed_tasks):
            print(f"  Fixed Task {i}:")
            print(f"    ID: {task.get('_id')}")
            print(f"    Name: {task.get('task_name')}")
            print(f"    Start: {task.get('task_start_time')}")
            print(f"    Duration: {task.get('task_duration')}")
            print(f"    Status: {task.get('status')}")
        
        for i, task in enumerate(flex_tasks):
            print(f"  Flexible Task {i}:")
            print(f"    ID: {task.get('_id')}")
            print(f"    Name: {task.get('task_name')}")
            print(f"    Start: {task.get('start_time')}")
            print(f"    Duration: {task.get('expected_duration')}")
            print(f"    Status: {task.get('status')}")
        
        return {
            "fixed_count": len(fixed_tasks),
            "flexible_count": len(flex_tasks),
            "fixed_tasks": fixed_tasks,
            "flexible_tasks": flex_tasks
        }
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{task_id}")
async def update_task(task_id: str, task_type: str, payload: dict):
    if task_type not in ["fixed", "flex"]:
        raise HTTPException(status_code=400, detail="task_type is required")
    try:
        collection = FIXED_TASK_COLLECTION if task_type == "fixed" else FLEXIBLE_TASK_COLLECTION

        updates = {}
        # 通用字段
        for k in ["task_name","task_type","expected_difficulty","task_location","task_priority","status"]:
            if k in payload: updates[k] = payload[k]

        if task_type == "fixed":
            # 支持前端传来的 startTime(YYYYMMDDHHMM) + duration(分钟/小时)
            st = payload.get("startTime")
            dur = payload.get("duration")
            if st: updates["task_start_time"] = st
            if dur is not None:
                duration_minutes = int(float(dur))
                try:
                    start_dt = datetime.strptime(st or payload.get("task_start_time"), DATETIME_FORMAT)
                    end_dt = start_dt + timedelta(minutes=duration_minutes)
                    updates["task_duration"] = duration_minutes
                    updates["task_end_time"] = end_dt.strftime(DATETIME_FORMAT)
                except Exception:
                    pass
        else:
            # flexible：支持 deadline / expected_duration
            if "deadline" in payload:
                updates["task_deadline"] = payload["deadline"]
            if "duration" in payload:
                updates["expected_duration"] = float(payload["duration"])

        result = await db[collection].update_one({"_id": ObjectId(task_id)}, {"$set": updates})
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"task_id": task_id, "updated_fields": list(updates.keys())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 在现有 tasks.py 文件末尾添加以下代码 ====================

@router.post("/check-completion/{user_id}")
async def check_and_complete_tasks(user_id: str):
    """
    检查并自动完成已过期的任务
    - 检查 flexible 任务：如果当前时间 >= start_time + duration，则标记为 completed
    - 检查 fixed 任务：如果当前时间 >= task_end_time，则标记为 completed
    """
    try:
        query = make_user_query(user_id)
        now = datetime.now()
        
        print(f"\n🕐 Checking task completion for user {user_id} at {now.strftime(DATETIME_FORMAT)}")
        print(f"🕐 Current time object: {now}")
        
        completed_count = 0
        
        # ========== 检查 Flexible 任务 ==========
        # ✅ 修改：查询所有有 start_time 的任务，不限制 status
        flex_query_base = query.copy()
        if "$or" in flex_query_base:
            flex_query = {
                "$and": [
                    flex_query_base,
                    {"start_time": {"$ne": None, "$exists": True}}
                ]
            }
        else:
            flex_query = {
                **flex_query_base,
                "start_time": {"$ne": None, "$exists": True}
            }
        
        flex_tasks = await db[FLEXIBLE_TASK_COLLECTION].find(flex_query).to_list(None)
        
        print(f"📋 Checking {len(flex_tasks)} flexible tasks...")
        
        for task in flex_tasks:
            task_name = task.get("task_name", "Unknown")
            start_time = task.get("start_time")
            duration = task.get("expected_duration", 60)
            
            if not start_time:
                continue
            
            try:
                # 解析开始时间
                start_dt = datetime.strptime(start_time, DATETIME_FORMAT)
                
                # 计算结束时间
                if duration < 10:  # 小时
                    end_dt = start_dt + timedelta(hours=duration)
                else:  # 分钟
                    end_dt = start_dt + timedelta(minutes=duration)
                
                # 如果当前时间已经过了任务结束时间
                if now >= end_dt:
                    result = await db[FLEXIBLE_TASK_COLLECTION].update_one(
                        {"_id": task["_id"]},
                        {
                            "$set": {
                                "status": "completed",
                                "completed_at": now.strftime(DATETIME_FORMAT)
                            }
                        }
                    )
                    
                    if result.modified_count > 0:
                        completed_count += 1
                        print(f"  ✅ Auto-completed flexible task: {task_name} (ended at {end_dt.strftime(DATETIME_FORMAT)})")
                
            except Exception as e:
                print(f"  ⚠️ Error processing flexible task {task_name}: {e}")
                continue
        
        # ========== 检查 Fixed 任务 ==========
        fixed_query = {**query, "status": {"$in": ["assigned"]}}
        fixed_tasks = await db[FIXED_TASK_COLLECTION].find(fixed_query).to_list(None)
        
        print(f"📋 Checking {len(fixed_tasks)} fixed tasks...")
        
        for task in fixed_tasks:
            task_name = task.get("task_name", "Unknown")
            end_time_str = task.get("task_end_time")
            
            # 如果没有 end_time，尝试从 start_time 和 duration 计算
            if not end_time_str and task.get("task_start_time") and task.get("task_duration"):
                try:
                    start_dt = datetime.strptime(task.get("task_start_time"), DATETIME_FORMAT)
                    duration = int(task.get("task_duration", 0))
                    end_dt = start_dt + timedelta(minutes=duration)
                    end_time_str = end_dt.strftime(DATETIME_FORMAT)
                    
                    # 保存计算的 end_time
                    await db[FIXED_TASK_COLLECTION].update_one(
                        {"_id": task["_id"]},
                        {"$set": {"task_end_time": end_time_str}}
                    )
                except Exception as e:
                    print(f"  ⚠️ Error calculating end_time for {task_name}: {e}")
                    continue
            
            if not end_time_str:
                continue
            
            try:
                end_dt = datetime.strptime(end_time_str, DATETIME_FORMAT)
                
                # 如果当前时间已经过了任务结束时间
                if now >= end_dt:
                    result = await db[FIXED_TASK_COLLECTION].update_one(
                        {"_id": task["_id"]},
                        {
                            "$set": {
                                "status": "completed",
                                "completed_at": now.strftime(DATETIME_FORMAT)
                            }
                        }
                    )
                    
                    if result.modified_count > 0:
                        completed_count += 1
                        print(f"  ✅ Auto-completed fixed task: {task_name} (ended at {end_time_str})")
                
            except Exception as e:
                print(f"  ⚠️ Error processing fixed task {task_name}: {e}")
                continue
        
        print(f"✅ Completion check done: {completed_count} tasks auto-completed\n")
        
        return {
            "success": True,
            "checked_tasks": len(flex_tasks) + len(fixed_tasks),
            "completed_tasks": completed_count,
            "message": f"Auto-completed {completed_count} tasks",
            "timestamp": now.strftime(DATETIME_FORMAT)
        }
    
    except Exception as e:
        print(f"❌ Error in check_and_complete_tasks: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/manual-complete/{task_id}")
async def manual_complete_task(task_id: str, task_type: str = None):
    """
    手动标记任务为完成
    task_type: "fixed" 或 "flex"
    """
    if task_type not in ["fixed", "flex"]:
        raise HTTPException(status_code=400, detail="task_type is required (fixed or flex)")
    
    try:
        now = datetime.now()
        current_time = now.strftime(DATETIME_FORMAT)
        
        collection = FIXED_TASK_COLLECTION if task_type == "fixed" else FLEXIBLE_TASK_COLLECTION
        
        # 更新任务状态为 completed
        result = await db[collection].update_one(
            {"_id": ObjectId(task_id)},
            {
                "$set": {
                    "status": "completed",
                    "completed_at": current_time
                }
            }
        )
        
        if result.modified_count > 0:
            print(f"✅ Manually completed {task_type} task {task_id}")
            return {
                "success": True,
                "task_id": task_id,
                "message": "Task marked as completed",
                "completed_at": current_time
            }
        else:
            raise HTTPException(status_code=404, detail="Task not found or already completed")
    
    except Exception as e:
        print(f"❌ Error in manual_complete_task: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-complete")
async def batch_complete_tasks(task_ids: list[str], task_types: list[str]):
    """
    批量标记任务为完成
    task_ids: 任务 ID 列表
    task_types: 对应的任务类型列表 ["fixed", "flex", ...]
    """
    if len(task_ids) != len(task_types):
        raise HTTPException(status_code=400, detail="task_ids and task_types must have same length")
    
    try:
        now = datetime.now()
        current_time = now.strftime(DATETIME_FORMAT)
        
        completed_count = 0
        
        for task_id, task_type in zip(task_ids, task_types):
            if task_type not in ["fixed", "flex"]:
                continue
            
            collection = FIXED_TASK_COLLECTION if task_type == "fixed" else FLEXIBLE_TASK_COLLECTION
            
            result = await db[collection].update_one(
                {"_id": ObjectId(task_id)},
                {
                    "$set": {
                        "status": "completed",
                        "completed_at": current_time
                    }
                }
            )
            
            if result.modified_count > 0:
                completed_count += 1
        
        print(f"✅ Batch completed {completed_count}/{len(task_ids)} tasks")
        
        return {
            "success": True,
            "completed_count": completed_count,
            "total_count": len(task_ids),
            "message": f"Completed {completed_count} out of {len(task_ids)} tasks"
        }
    
    except Exception as e:
        print(f"❌ Error in batch_complete_tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/{user_id}/all")
async def get_all_tasks(user_id: str):
    """
    获取用户的所有任务（不按日期过滤）
    用于dashboard等需要查看所有任务的场景
    """
    try:
        query = make_user_query(user_id)
        now = datetime.now()
        
        print(f"\n📊 Loading ALL tasks for dashboard - user {user_id}")
        
        # 获取所有任务，不进行日期过滤
        fixed_tasks = await db[FIXED_TASK_COLLECTION].find(query).to_list(None)
        flex_tasks = await db[FLEXIBLE_TASK_COLLECTION].find(query).to_list(None)
        
        # 转换 ObjectId 为字符串
        for t in fixed_tasks + flex_tasks:
            t["_id"] = str(t["_id"])
            t["id"] = t["_id"]
            if "predicted_energy" not in t:
                t["predicted_energy"] = None
            if "predicted_pressure" not in t:
                t["predicted_pressure"] = None
        
        print(f"📊 Dashboard: {len(fixed_tasks)} fixed, {len(flex_tasks)} flexible tasks")
        
        return {
            "fixed": fixed_tasks,
            "flexible": flex_tasks,
            "ai_predictions": True,
            "is_today_view": False,
            "total_count": len(fixed_tasks) + len(flex_tasks)
        }
    except Exception as e:
        print(f"❌ Error loading all tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
