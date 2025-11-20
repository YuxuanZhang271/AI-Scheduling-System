# cleanup_all_tasks.py
import asyncio
from datetime import datetime, timedelta
from database import db
from models import FIXED_TASK_COLLECTION, FLEXIBLE_TASK_COLLECTION

async def cleanup():
    # 修复固定任务时间格式
    fixed = await db[FIXED_TASK_COLLECTION].find({
        "user_id": "68e9212ba448a137ef81a37c"
    }).to_list(None)
    
    print(f"Found {len(fixed)} fixed tasks")
    for task in fixed:
        old_time = task.get('task_start_time', '')
        if 'T' in old_time or '-' in old_time:
            # 转换格式
            dt = datetime.fromisoformat(old_time.replace('Z', '+00:00'))
            new_time = dt.strftime("%Y%m%d%H%M")
            await db[FIXED_TASK_COLLECTION].update_one(
                {"_id": task["_id"]},
                {"$set": {"task_start_time": new_time}}
            )
            print(f"  ✓ {task['task_name']}: {old_time} → {new_time}")
    
    # 修复灵活任务 deadline 格式
    flexible = await db[FLEXIBLE_TASK_COLLECTION].find({
        "user_id": "68e9212ba448a137ef81a37c"
    }).to_list(None)
    
    print(f"Found {len(flexible)} flexible tasks")
    for task in flexible:
        # 为每个灵活任务设置一个合理的 deadline（明天）
        future = datetime.utcnow() + timedelta(days=1)
        deadline = future.strftime("%Y%m%d%H%M")
        
        await db[FLEXIBLE_TASK_COLLECTION].update_one(
            {"_id": task["_id"]},
            {
                "$set": {
                    "task_deadline": deadline,
                    "start_time": None,
                    "end_time": None,
                    "status": "unassigned"
                }
            }
        )
        print(f"  ✓ {task['task_name']}: deadline = {deadline}")
    
    print("\nCleanup complete!")

asyncio.run(cleanup())