# routers/scheduler.py
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from bson import ObjectId
import joblib
import numpy as np
import os
from database import db
from models import FIXED_TASK_COLLECTION, FLEXIBLE_TASK_COLLECTION
from utils.scheduler_updated import Scheduler, DATETIME_FORMAT

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])

# ===========================================================
# 🔹 统一模型加载逻辑
# ===========================================================
HAS_MODELS = False
energy_model = None
pressure_model = None
label_encoder = None


def load_models():
    """全局加载模型，只加载一次"""
    global HAS_MODELS, energy_model, pressure_model, label_encoder
    try:
        base = "models"
        energy_path = os.path.join(base, "energy_loss_model.pkl")
        pressure_path = os.path.join(base, "pressure_increase_model.pkl")
        label_path = os.path.join(base, "task_label_encoder.pkl")

        if all(os.path.exists(p) for p in [energy_path, pressure_path, label_path]):
            energy_model = joblib.load(energy_path)
            pressure_model = joblib.load(pressure_path)
            label_encoder = joblib.load(label_path)
            HAS_MODELS = True
            print("✅ ML models loaded from /models directory")
        else:
            missing = [p for p in [energy_path, pressure_path, label_path] if not os.path.exists(p)]
            print(f"⚠️ Missing model files: {missing}")
            HAS_MODELS = False
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        HAS_MODELS = False


# 启动时加载一次
load_models()

# ===========================================================
# 🔹 统一预测函数（供 Scheduler 与路由共用）
# ===========================================================
def predict_energy_pressure(task_type: str, difficulty: int, duration_minutes: float):
    """使用 AI 模型预测能量消耗与压力变化"""
    if not HAS_MODELS:
        return {"energy": 1.0, "pressure": 0.5}
    try:
        # task_type 编码
        type_map = {v: i for i, v in enumerate(label_encoder.classes_)}
        type_encoded = type_map.get(str(task_type).lower(), len(type_map))
        X = np.array([[type_encoded, difficulty, duration_minutes]])

        energy_pred = float(energy_model.predict(X)[0])
        pressure_pred = float(pressure_model.predict(X)[0])

        # 限制范围 [0,5]
        energy_pred = max(0, min(5, energy_pred))
        pressure_pred = max(0, min(5, pressure_pred))

        return {"energy": energy_pred, "pressure": pressure_pred}
    except Exception as e:
        print(f"⚠️ Prediction error: {e}")
        return {"energy": 1.0, "pressure": 0.5}


# ===========================================================
# 🚀 调度主接口
# ===========================================================
@router.post("/run/{user_id}")
async def run_scheduler(user_id: str, use_model: bool = True):
    """
    主调度端点，执行任务调度流程
    """
    try:
        print(f"\n{'='*70}")
        print(f"🚀 STARTING SCHEDULER for user: {user_id}")
        print(f"🔧 ML Model Enabled: {use_model and HAS_MODELS}")
        print(f"{'='*70}")

        # 1️⃣ 初始化调度器
        sch = Scheduler(user_id)
        await sch.initScheduler()

        print(f"📊 Initial status → Timetable: {len(sch.timetable)}, "
              f"Windows: {len(sch.windows)}, Unscheduled: {len(sch.unscheduled_tasks)}")

        # 2️⃣ 可选：运行模型补充预测值
        if use_model and HAS_MODELS:
            print("\n🤖 Enriching tasks with ML model predictions...")
            for t in sch.unscheduled_tasks:
                pred = predict_energy_pressure(
                    task_type=t.get("type", "work"),
                    difficulty=int(t.get("difficulty", 3)),
                    duration_minutes=int(t.get("duration", 60))
                )
                t["energy"], t["pressure"] = pred["energy"], pred["pressure"]

        # 3️⃣ 排列任务
        sch.arrangeTasksToWindows()

        # 4️⃣ 窗口内排序
        sch.scheduleTasksInWindow()

        # 5️⃣ 分配休息时间
        sch.distributeRestTimes()

        # 6️⃣ 更新数据库
        print("\n💾 Writing back to MongoDB...")
        updated, failed = 0, 0
        for w in sch.windows:
            for task in w["tasks"]:
                try:
                    task_id = task.get("task_id")
                    start_time = task.get("start_time")
                    duration = int(task.get("duration", 60))
                    if not task_id or not start_time:
                        continue

                    st_dt = datetime.strptime(start_time, DATETIME_FORMAT)
                    et_dt = st_dt + timedelta(minutes=duration)
                    end_time = et_dt.strftime(DATETIME_FORMAT)

                    result = await db[FLEXIBLE_TASK_COLLECTION].update_one(
                        {"_id": ObjectId(task_id)},
                        {"$set": {
                            "start_time": start_time,
                            "end_time": end_time,
                            "status": "assigned",
                            "predicted_energy": task.get("energy", 1.0),
                            "predicted_pressure": task.get("pressure", 0.5),
                        }},
                    )
                    if result.modified_count > 0:
                        updated += 1
                    else:
                        failed += 1
                except Exception as e:
                    print(f"❌ DB update error: {e}")
                    failed += 1

        print(f"\n✅ Scheduler finished — Updated: {updated}, Failed: {failed}, "
              f"Unscheduled: {len(sch.unscheduled_tasks)}\n{'='*70}")

        return {
            "success": True,
            "updated": updated,
            "failed": failed,
            "unscheduled": len(sch.unscheduled_tasks),
            "used_model": use_model and HAS_MODELS,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ===========================================================
# 🧠 模型状态检测
# ===========================================================
@router.get("/model-status")
async def check_model_status():
    """返回模型加载状态"""
    return {
        "has_models": HAS_MODELS,
        "models": {
            "energy_model": "loaded" if energy_model else "missing",
            "pressure_model": "loaded" if pressure_model else "missing",
            "label_encoder": "loaded" if label_encoder else "missing",
        },
        "message": "Models ready" if HAS_MODELS else "⚠️ Models not found — fallback to defaults",
    }


# ===========================================================
# 🔍 调试：仅预测
# ===========================================================
@router.post("/debug/predict/{user_id}")
async def debug_predict_tasks(user_id: str):
    """仅输出预测结果，不修改数据库"""
    sch = Scheduler(user_id)
    await sch.initScheduler()

    print(f"\n🔮 Debug Predictions for {len(sch.unscheduled_tasks)} tasks")

    predictions = []
    for t in sch.unscheduled_tasks:
        pred = predict_energy_pressure(
            t.get("type", "work"),
            int(t.get("difficulty", 3)),
            int(t.get("duration", 60)),
        )
        t["predicted_energy"] = pred["energy"]
        t["predicted_pressure"] = pred["pressure"]
        predictions.append({
            "task_id": t.get("task_id"),
            "task_name": t.get("name"),
            "predicted_energy": pred["energy"],
            "predicted_pressure": pred["pressure"],
        })

    return {
        "success": True,
        "has_models": HAS_MODELS,
        "total": len(predictions),
        "predictions": predictions,
    }


# ===========================================================
# 🧩 调试：完整调度 + 预测
# ===========================================================
@router.post("/debug/schedule-with-predictions/{user_id}")
async def debug_schedule_with_predictions(user_id: str):
    """运行完整调度并返回预测详情"""
    sch = Scheduler(user_id)
    await sch.initScheduler()

    for t in sch.unscheduled_tasks:
        pred = predict_energy_pressure(
            t.get("type", "work"),
            int(t.get("difficulty", 3)),
            int(t.get("duration", 60)),
        )
        t["energy"], t["pressure"] = pred["energy"], pred["pressure"]

    sch.arrangeTasksToWindows()
    sch.scheduleTasksInWindow()
    sch.distributeRestTimes()

    results = []
    for i, w in enumerate(sch.windows):
        if w["tasks"]:
            results.append({
                "window": i,
                "start": w["start_time"].strftime(DATETIME_FORMAT),
                "end": w["end_time"].strftime(DATETIME_FORMAT),
                "score": w.get("score"),
                "tasks": [
                    {
                        "task_id": t.get("task_id"),
                        "name": t.get("name"),
                        "start_time": t.get("start_time"),
                        "duration": t.get("duration"),
                        "predicted_energy": t.get("energy"),
                        "predicted_pressure": t.get("pressure"),
                    }
                    for t in w["tasks"]
                ],
            })

    return {
        "success": True,
        "has_models": HAS_MODELS,
        "windows": results,
        "unscheduled": len(sch.unscheduled_tasks),
    }
