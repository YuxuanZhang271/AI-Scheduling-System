from fastapi import APIRouter, HTTPException
from datetime import datetime
from bson import ObjectId
from database import db
from models import FIXED_TASKS_COLLECTION, FLEX_TASKS_COLLECTION, USER_COLLECTION

router = APIRouter(prefix="/tasks", tags=["Tasks"])


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
    获取某个用户的所有任务（fixed + flexible）
    """
    try:
        query = make_user_query(user_id)

        fixed_tasks = await db[FIXED_TASKS_COLLECTION].find(query).to_list(None)
        flex_tasks = await db[FLEX_TASKS_COLLECTION].find(query).to_list(None)

        for t in fixed_tasks + flex_tasks:
            t["_id"] = str(t["_id"])
            t["id"] = t["_id"]

        print(f"✅ [GET] Loaded {len(fixed_tasks)} fixed + {len(flex_tasks)} flexible tasks for user {user_id}")
        return {"fixed": fixed_tasks, "flexible": flex_tasks}

    except Exception as e:
        print("❌ Error loading tasks:", e)
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/{user_id}")
async def create_task(user_id: str, task: dict):
    """
    创建任务，支持 fixed / flexible 两种模式
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
            new_task_doc = {
                "user_id": str(user_id),
                "task_name": task.get("name", ""),
                "task_type": task.get("category", "work"),
                "task_start_time": task.get("startTime", datetime.utcnow()),
                "task_duration": float(task.get("duration", 1)),
                "expected_difficulty": int(task.get("difficulty", 3)),
                "task_location": task.get("location", ""),
                "status": "assigned",
                "created_at": datetime.utcnow(),
            }

            result = await db[FIXED_TASKS_COLLECTION].insert_one(new_task_doc)
            task_id = str(result.inserted_id)

            return {
                "task_id": task_id,
                "task": {
                    "id": task_id,
                    "name": new_task_doc["task_name"],
                    "startTime": new_task_doc["task_start_time"],
                    "duration": new_task_doc["task_duration"],
                    "category": new_task_doc["task_type"],
                    "difficulty": new_task_doc["expected_difficulty"],
                    "location": new_task_doc.get("task_location", ""),
                    "status": new_task_doc["status"],
                },
                "message": "✅ Fixed task created successfully"
            }

        elif mode == "flexible":
            new_task_doc = {
                "user_id": str(user_id),
                "task_name": task.get("name", ""),
                "task_type": task.get("category", "work"),
                "task_deadline": task.get("deadline", datetime.utcnow()),
                "expected_duration": float(task.get("duration", 1)),
                "expected_difficulty": int(task.get("difficulty", 3)),
                "task_priority": int(task.get("priority", 1)),
                "task_location": task.get("location", ""),
                "status": "unassigned",
                "created_at": datetime.utcnow(),
            }

            result = await db[FLEX_TASKS_COLLECTION].insert_one(new_task_doc)
            task_id = str(result.inserted_id)

            return {
                "task_id": task_id,
                "task": {
                    "id": task_id,
                    "name": new_task_doc["task_name"],
                    "deadline": new_task_doc["task_deadline"],
                    "duration": new_task_doc["expected_duration"],
                    "category": new_task_doc["task_type"],
                    "difficulty": new_task_doc["expected_difficulty"],
                    "priority": new_task_doc["task_priority"],
                    "location": new_task_doc.get("task_location", ""),
                    "status": new_task_doc["status"],
                },
                "message": "✅ Flexible task created successfully"
            }

    except Exception as e:
        print("❌ Error creating task:", e)
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
        collection = FIXED_TASKS_COLLECTION if task_type == "fixed" else FLEX_TASKS_COLLECTION
        result = await db[collection].delete_one({"_id": ObjectId(task_id)})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Task not found")

        print(f"🗑️ Deleted {task_type} task {task_id}")
        return {"task_id": task_id, "message": "Task deleted successfully"}

    except Exception as e:
        print(f"❌ Error deleting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
