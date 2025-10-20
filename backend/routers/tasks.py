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
async def get_tasks(user_id: str):
    """
    获取某个用户的所有任务，自动更新状态
    ✅ 如果 fixed 任务缺少 end_time，从 start_time 和 duration 动态计算
    """
    try:
        query = make_user_query(user_id)
        now = datetime.now()
        print(f"\n🕐 Current time: {now.strftime(DATETIME_FORMAT)}")

        # 获取 fixed & flexible
        fixed_tasks = await db[FIXED_TASK_COLLECTION].find(query).to_list(None)
        flex_tasks = await db[FLEXIBLE_TASK_COLLECTION].find(query).to_list(None)

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

        # ✅ 自动更新 flexible 任务状态 - assigned 时间到则变 processing
        print(f"📋 Checking {len(flex_tasks)} flexible tasks:")
        for t in flex_tasks:
            task_name = t.get('task_name', 'N/A')
            start_time = t.get("start_time")
            current_status = t.get("status", "unassigned")
            
            print(f"  - {task_name}: status={current_status}, start_time={start_time}")
            
            if start_time and isinstance(start_time, str):
                try:
                    st_dt = datetime.strptime(start_time, DATETIME_FORMAT)
                    if current_status == "assigned" and now >= st_dt:
                        await db[FLEXIBLE_TASK_COLLECTION].update_one(
                            {"_id": t["_id"]},
                            {"$set": {"status": "processing"}}
                        )
                        t["status"] = "processing"
                        print(f"    ✅ Updated to processing")
                except Exception as e:
                    print(f"    ❌ Error: {e}")

        # --- 转换 ObjectId 为字符串 ---
        for t in fixed_tasks + flex_tasks:
            t["_id"] = str(t["_id"])
            t["id"] = t["_id"]

        print(f"\n📥 GET /tasks/{user_id} complete")
        
        return {"fixed": fixed_tasks, "flexible": flex_tasks}

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