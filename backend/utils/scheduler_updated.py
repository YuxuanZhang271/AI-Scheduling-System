#!/usr/bin/env python
# coding: utf-8

import datetime as dt
import math
import numpy as np
import itertools
from joblib import load


from database import db
from models import FIXED_TASK_COLLECTION, FLEXIBLE_TASK_COLLECTION


DATETIME_FORMAT = "%Y%m%d%H%M"
TASK_TYPE = ["food", "fun", "work"]
class AIScheduler:
    def __init__(self, user_id):
        self.user_id = user_id
        # 加载模型
        try:
            self.energy_model = load("models/energy_loss_model.pkl")
            self.pressure_model = load("models/pressure_increase_model.pkl")
            print("✅ AI Models loaded successfully")
        except Exception as e:
            print("⚠️ Failed to load AI models:", e)
            self.energy_model = None
            self.pressure_model = None

    def predict_task_impact(self, task):
        """根据任务特征预测能量消耗与压力变化"""
        if not self.energy_model or not self.pressure_model:
            return None, None

        try:
            # 构建输入特征向量
            # 这里根据你模型训练时的特征顺序调整！
            X = np.array([[task.get("difficulty", 3),
                           task.get("duration", 1),
                           task.get("priority", 1)]])
            energy_pred = float(self.energy_model.predict(X)[0])
            pressure_pred = float(self.pressure_model.predict(X)[0])
            return energy_pred, pressure_pred
        except Exception as e:
            print("⚠️ AI prediction error:", e)
            return None, None


def _prepare_attributes(task: dict) -> dict:
    task_id    = task.get("task_id", "")

    task_type  = TASK_TYPE.index(task.get("type", "work")) - 1
    difficulty = (task.get("difficulty", 3) - 3) // 2
    # ✅ 修复：duration 是分钟，需要用分钟计算
    duration_minutes = int(task.get("duration", 60))
    duration   = duration_minutes // 30 - 2

    energy     = task.get("energy", 1)
    pressure   = task.get("pressure", 1)

    return {
        "task_id":    task_id,
        "attributes": np.array([task_type, difficulty, duration]),
        "energy":     energy,
        "pressure":   pressure,
        "duration":   duration_minutes,  # ✅ 保存分钟数
    }


def _calculateScore(tasks: list[dict], energy_weight=0.5) -> float:
    if len(tasks) <= 1:
        return 0.0
        
    total_energy     = 0.0
    total_pressure   = 0.0
    previus_energy   = 0.0
    previus_pressure = 0.0
    previous_attributes = np.array([0, 0, 0])
    
    for i in range(len(tasks) - 1):
        if i == 0:
            total_energy   += tasks[i].get("energy", 1)
            total_pressure += tasks[i].get("pressure", 1)
        else: 
            prev_attr = previous_attributes
            curr_attr = tasks[i].get("attributes", np.array([0, 0, 0]))
            
            norm_prev = np.linalg.norm(prev_attr)
            norm_curr = np.linalg.norm(curr_attr)
            
            if norm_prev > 1e-6 and norm_curr > 1e-6:
                similarity = np.dot(prev_attr, curr_attr) / (norm_prev * norm_curr)
            else:
                similarity = 0.0
                
            total_energy   += tasks[i].get("energy", 1) + similarity * previus_energy
            total_pressure += tasks[i].get("pressure", 1) + similarity * previus_pressure
        
        previus_energy      = tasks[i].get("energy", 1)
        previus_pressure    = tasks[i].get("pressure", 1)
        previous_attributes = tasks[i].get("attributes", np.array([0, 0, 0]))

    return energy_weight * total_energy + (1 - energy_weight) * total_pressure


def _sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x))


def _r_from_lambda(lmbd, C, b, c, rmin=0.0, rmax=float("inf")):
    if lmbd >= (C * b) / 4.0 or C <= 0.0 or b <= 0.0:
        return 0.0

    q    = lmbd / (C * b)
    q    = max(0.0, min(0.249999999, q))
    s    = 0.5 + 0.5 * math.sqrt(1.0 - 4.0 * q)
    
    denominator = 1.0 - s
    if abs(denominator) < 1e-10:
        denominator = 1e-10
    
    odds = s / denominator
    r    = c + (1.0 / b) * math.log(odds)

    return max(rmin, min(rmax, r))


def _allocate_rest_sigmoid(rest_budget, slots_params, tol=1e-6, max_iter=100):
    if rest_budget <= 0 or not slots_params:
        return [0.0] * len(slots_params)

    lam_hi = max((p["C"] * p["b"]) / 4.0 for p in slots_params if p["C"] > 0 and p["b"] > 0)
    lam_lo = 0.0

    def sum_r(lmbd):
        return sum(_r_from_lambda(lmbd, p["C"], p["b"], p["c"], p.get("rmin", 0.0), p.get("rmax", float("inf")))
                   for p in slots_params)

    total_cap = sum_r(0.0)
    if total_cap <= rest_budget + tol:
        rs = []
        for p in slots_params:
            rs.append(_r_from_lambda(0.0, p["C"], p["b"], p["c"], p.get("rmin", 0.0), p.get("rmax", float("inf"))))
        return rs

    for _ in range(max_iter):
        lam_mid = 0.5 * (lam_lo + lam_hi)
        s_mid = sum_r(lam_mid)
        if abs(s_mid - rest_budget) <= tol:
            break
        if s_mid > rest_budget:
            lam_lo = lam_mid
        else:
            lam_hi = lam_mid

    lam_star = 0.5 * (lam_lo + lam_hi)
    rs = []
    for p in slots_params:
        rs.append(_r_from_lambda(lam_star, p["C"], p["b"], p["c"], p.get("rmin", 0.0), p.get("rmax", float("inf"))))
    scale = rest_budget / max(sum(rs), 1e-12)
    return [r * scale for r in rs]


class Scheduler:
    def __init__(self, user_id):
        self.user_id           = user_id
        self.timetable         = []
        self.windows           = []
        self.unscheduled_tasks = []
        self.energy_weight     = 0.5
    
    async def findFixedTasks(self):
        """异步查询固定任务"""
        query = {"user_id": str(self.user_id)}
        return await db[FIXED_TASK_COLLECTION].find(query).to_list(None)
    
    async def findScheduledTasks(self):
        """异步查询已分配时间的灵活任务"""
        query = {
            "user_id": str(self.user_id), 
            "start_time": {"$ne": None}
        }
        return await db[FLEXIBLE_TASK_COLLECTION].find(query).to_list(None)
    
    async def findUnscheduledTasks(self):
        """异步查询未分配时间的灵活任务"""
        query = {
            "user_id": str(self.user_id), 
            "start_time": {"$eq": None}
        }
        return await db[FLEXIBLE_TASK_COLLECTION].find(query).to_list(None)
    
    def _normalize_task(self, t, is_fixed=False):
        """将数据库任务转换为调度器期望的格式"""
        task_id = str(t.get("_id", ""))
        
        if is_fixed:
            start_time = t.get("task_start_time", "")
            duration_raw = float(t.get("task_duration", 60))
        else:
            start_time = t.get("start_time", "")
            duration_raw = float(t.get("expected_duration", 60))
        
        # ✅ 修复：统一处理持续时间（全部转换为分钟）
        # 如果 duration_raw 小于 10，认为是小时，否则认为是分钟
        if duration_raw < 10:
            duration = int(duration_raw * 60)  # 小时转分钟
        else:
            duration = int(duration_raw)       # 直接使用分钟
        
        print(f"    🕐 Task {task_id[:8]}: raw_duration={duration_raw}, final_duration={duration}min")
        
        # 计算结束时间
        if start_time:
            try:
                st_dt = dt.datetime.strptime(start_time, DATETIME_FORMAT)
                et_dt = st_dt + dt.timedelta(minutes=duration)
                end_time = et_dt.strftime(DATETIME_FORMAT)
            except:
                end_time = ""
        else:
            end_time = ""
        
        return {
            "task_id": task_id,
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,  # ✅ 保存为分钟数
            "deadline": t.get("task_deadline", ""),
            "type": t.get("task_type", "work"),
            "difficulty": float(t.get("expected_difficulty", 3)),
            "priority": int(t.get("task_priority", 2)),
            "energy": float(t.get("energy", 1)),
            "pressure": float(t.get("pressure", 1)),
            "name": t.get("task_name", ""),
        }
    
    async def initScheduler(self):
        """异步初始化调度器"""
        print(f"📋 Initializing scheduler for user {self.user_id}")
        
        fixed_tasks_raw = await self.findFixedTasks()
        scheduled_tasks_raw = await self.findScheduledTasks()
        
        print(f"  Found {len(fixed_tasks_raw)} fixed tasks, {len(scheduled_tasks_raw)} scheduled flexible tasks")
        
        fixed_tasks = [self._normalize_task(t, is_fixed=True) for t in fixed_tasks_raw]
        scheduled_tasks = [self._normalize_task(t, is_fixed=False) for t in scheduled_tasks_raw]
        
        assigned_tasks = fixed_tasks + scheduled_tasks
        assigned_tasks.sort(key=lambda x: (x["start_time"]))
        self.timetable = assigned_tasks

        windows = []
        for i in range(len(assigned_tasks) - 1):
            try:
                end_time_str = assigned_tasks[i]["end_time"]
                start_time_str = assigned_tasks[i + 1]["start_time"]
                
                if not end_time_str or not start_time_str:
                    continue
                
                end_time = dt.datetime.strptime(end_time_str, DATETIME_FORMAT)
                start_time = dt.datetime.strptime(start_time_str, DATETIME_FORMAT)
                
                if start_time > end_time:
                    windows.append({
                        "task_before": assigned_tasks[i],
                        "task_after":  assigned_tasks[i + 1],
                        "start_time":  end_time,
                        "end_time":    start_time, 
                        "tasks":       []
                    })
            except Exception as e:
                print(f"  Warning: Window creation error: {e}")
                continue
        
        self.windows = windows
        if assigned_tasks:
            last_task = assigned_tasks[-1]
            if last_task["end_time"]:
                try:
                    last_end = dt.datetime.strptime(last_task["end_time"], DATETIME_FORMAT)
                    day_end = dt.datetime.combine(last_end.date(), dt.time(23, 59))  # 当天23:59
                    if day_end > last_end:
                        windows.append({
                            "task_before": last_task,
                            "task_after": {"task_id": "end_of_day"},
                            "start_time": last_end,
                            "end_time": day_end,
                            "tasks": []
                        })
                except:
                    pass
        
        print(f"  Created {len(windows)} time windows")
        
        unassigned_tasks_raw = await self.findUnscheduledTasks()
        unassigned_tasks = [self._normalize_task(t, is_fixed=False) for t in unassigned_tasks_raw]
        unassigned_tasks.sort(key=lambda x: (x["deadline"], x["priority"], -x["duration"]))
        self.unscheduled_tasks = unassigned_tasks
        print(f"  Found {len(unassigned_tasks)} unscheduled tasks")

        # === 🧠 运行 AI 模型预测能量与压力 ===
        print("🤖 Running AI prediction for all tasks...")
        ai = AIScheduler(self.user_id)

        # 导入 predict_energy_pressure（用于兼容旧逻辑）
        try:
            from routers.scheduler import predict_energy_pressure
        except Exception:
            def predict_energy_pressure(**_):
                return {"energy": 1.0, "pressure": 0.5}

        # 合并所有任务
        all_tasks = fixed_tasks + scheduled_tasks + unassigned_tasks

        # 遍历并预测
        for task in all_tasks:
            e, p = ai.predict_task_impact(task)
            # 若 AI 模型未加载成功或返回 None → 使用 fallback 模型
            if e is None or p is None:
                try:
                    pred = predict_energy_pressure(
                        task_type=task.get("type", "work"),
                        difficulty=int(task.get("difficulty", 3)),
                        duration_minutes=int(task.get("duration", 60))
                    )
                    e = pred["energy"]
                    p = pred["pressure"]
                except Exception:
                    e, p = 1.0, 0.5

            task["predicted_energy"] = e
            task["predicted_pressure"] = p

        # === 💾 写回 MongoDB ===
        print("💾 Saving predictions to MongoDB...")
        for task in all_tasks:
            try:
                coll = FIXED_TASK_COLLECTION if task.get("mode") == "fixed" else FLEXIBLE_TASK_COLLECTION
                task_type = task.get("type") or task.get("category") or "work"
                await db[coll].update_one(
                    {"_id": ObjectId(task["task_id"])},
                    {"$set": {
                        "predicted_energy": task.get("predicted_energy", 1.0),
                        "predicted_pressure": task.get("predicted_pressure", 0.5),
                        "type": task_type,
                    }}
                )
                print(f"  ✅ Updated {task.get('name')} predictions.")
            except Exception as e:
                print(f"  ❌ Failed to update {task.get('name')}: {e}")
            


    def arrangeTasksToWindows(self):
        """将未分配任务分配到时间窗口"""
        print("📄 Arranging tasks to windows...")
        unscheduled_tasks = self.unscheduled_tasks.copy()
        windows = self.windows.copy()

        for task in unscheduled_tasks:
            task_id  = task["task_id"]
            duration = task["duration"]  # ✅ 现在这是分钟数
            deadline_str = task["deadline"]
            
            if not deadline_str:
                continue
            
            try:
                deadline = dt.datetime.strptime(deadline_str, DATETIME_FORMAT)
            except Exception as e:
                print(f"  Warning: Deadline parse error for task {task_id}: {e}")
                continue

            scheduled = False

            for window in windows:
                # 检查1：窗口开始时间要在截止日期之前
                if window["start_time"] >= deadline:
                    continue  # ✅ 修复：用 continue 而不是 break
                
                # 检查2：计算窗口可用时间
                window_duration = (window["end_time"] - window["start_time"]).total_seconds() / 60
                used_duration = sum(t["duration"] for t in window["tasks"])
                available_duration = window_duration - used_duration
                
                # 检查3：任务必须能放进可用空间（留 25% 缓冲用于休息）
                required_duration = duration * 1.25
                
                # 检查4：最终时间不能超过窗口结束或任务截止
                if required_duration <= available_duration:
                    tasks_end_time = window["start_time"] + dt.timedelta(
                        minutes=used_duration + duration
                    )
                    
                    if tasks_end_time <= window["end_time"] and tasks_end_time <= deadline:
                        window["tasks"].append(task)
                        scheduled = True
                        print(f"  ✓ Task {task_id[:8]} ({duration}min) scheduled in window {window['start_time'].strftime(DATETIME_FORMAT)}")
                        break
            
            if not scheduled:
                print(f"  ✗ Task {task_id[:8]} ({duration}min) could not be scheduled")
        
        self.unscheduled_tasks = unscheduled_tasks
        self.windows = windows
        print(f"  {len(self.unscheduled_tasks)} tasks remaining unscheduled")

    def scheduleTasksInWindow(self):
        """在每个窗口内最优排序任务"""
        print("⏱️ Scheduling tasks within windows...")
        
        for window_idx, window in enumerate(self.windows):
            tasks_within = window["tasks"]
            
            if len(tasks_within) == 0:
                continue
            
            if len(tasks_within) == 1:
                window["score"] = 0
                continue

            task_before  = _prepare_attributes(window["task_before"].copy())
            task_after   = _prepare_attributes(window["task_after"].copy())
            tasks_within_prepared = [_prepare_attributes(t.copy()) for t in tasks_within]

            # 策略1：小规模精确搜索
            if len(tasks_within_prepared) <= 8:
                best_score = float("inf")
                best_perm  = None
                for perm in itertools.permutations(tasks_within_prepared):
                    candidate = [task_before] + list(perm) + [task_after]
                    score = _calculateScore(candidate, self.energy_weight)
                    if score < best_score:
                        best_score = score
                        best_perm  = list(perm)
                
                if best_perm:
                    ordered_tasks = []
                    for prep_task in best_perm:
                        task_id = prep_task.get("task_id")
                        original = next((t for t in tasks_within if t["task_id"] == task_id), None)
                        if original:
                            ordered_tasks.append(original)
                    window["tasks"] = ordered_tasks
                
                window["score"] = best_score
                print(f"  Window {window_idx}: exact search, score={best_score:.2f}")
            else:
                # 策略2：贪心算法
                remaining = tasks_within_prepared[:]
                sequence  = [task_before]
                
                while remaining:
                    best_next  = None
                    best_score = float("inf")
                    for cand in remaining:
                        candidate = sequence + [cand] + [task_after]
                        score = _calculateScore(candidate, self.energy_weight)
                        if score < best_score:
                            best_score = score
                            best_next  = cand
                    sequence.append(best_next)
                    remaining.remove(best_next)

                ordered_tasks = []
                for prep_task in sequence[1:]:
                    task_id = prep_task.get("task_id")
                    original = next((t for t in tasks_within if t["task_id"] == task_id), None)
                    if original:
                        ordered_tasks.append(original)
                window["tasks"] = ordered_tasks
                
                final_candidate = [task_before] + sequence[1:] + [task_after]
                window["score"] = _calculateScore(final_candidate, self.energy_weight)
                print(f"  Window {window_idx}: greedy algorithm, score={window['score']:.2f}")
    
    def distributeRestTimes(self):
        """分配休息时间并计算每个任务的开始时间"""
        print("😴 Distributing rest times...")
        
        for window_idx, window in enumerate(self.windows):
            tasks = window["tasks"]
            if not tasks:
                continue

            total_task_duration = sum(t["duration"] for t in tasks)
            total_window_duration = (window["end_time"] - window["start_time"]).total_seconds() / 60.0
            rest_budget = total_window_duration - total_task_duration
            
            print(f"  Window {window_idx}: window={total_window_duration:.0f}min, tasks={total_task_duration:.0f}min, rest={rest_budget:.0f}min")
            
            # ✅ 添加任务详情调试
            for i, task in enumerate(tasks):
                print(f"    Task {i}: {task['name']} - {task['duration']}min")
            
            if rest_budget < 0:
                print(f"  ⚠️ Warning: Window {window_idx}: insufficient time, tasks exceed window by {-rest_budget:.0f}min")
                rest_distribution = [0.0] * (len(tasks) + 1)
            elif rest_budget <= 0:
                rest_distribution = [0.0] * (len(tasks) + 1)
            else:
                slots_params = []
                for j in range(len(tasks) + 1):
                    i = min(j, len(tasks) - 1)
                    t = tasks[i]

                    alpha_E = t.get("alpha_E", 1.0)
                    alpha_P = t.get("alpha_P", 1.0)
                    b = t.get("rest_slope_b", 0.08)
                    c = t.get("rest_center_c", 10.0)
                    C = self.energy_weight * alpha_E + (1 - self.energy_weight) * alpha_P

                    slots_params.append({
                        "C": C, "b": b, "c": c,
                        "rmin": 0.0,
                        "rmax": t.get("rest_rmax", float("inf")),
                    })

                rest_distribution = _allocate_rest_sigmoid(rest_budget, slots_params, tol=1e-4, max_iter=80)

            rest_start_time = window["start_time"]
            for j in range(len(tasks)):
                rest_minutes = rest_distribution[j] if j < len(rest_distribution) else 0
                tasks[j]["start_time"] = (rest_start_time + dt.timedelta(minutes=rest_minutes)).strftime(DATETIME_FORMAT)
                rest_start_time = dt.datetime.strptime(tasks[j]["start_time"], DATETIME_FORMAT) + dt.timedelta(minutes=tasks[j]["duration"])
                print(f"    ✅ Task {tasks[j]['name']} scheduled at {tasks[j]['start_time']} for {tasks[j]['duration']}min")

    def incrementalUpdate(self, deleted_tasks=None, new_fixed_tasks=None, new_flexible_tasks=None):
        """
        增量更新调度器 - 返回更新结果供前端使用
        
        Args:
            deleted_tasks: 删除的任务列表
            new_fixed_tasks: 新增的固定任务列表
            new_flexible_tasks: 新增的灵活任务列表
        
        Returns:
            dict: 包含更新后的日程信息
        """
        deleted_tasks = deleted_tasks or []
        new_fixed_tasks = new_fixed_tasks or []
        new_flexible_tasks = new_flexible_tasks or []
        
        deleted_ids = {t["task_id"] for t in deleted_tasks}
        affected_windows_for_rest = set()  
        affected_windows_for_reschedule = set()
        updated_task_ids = []
        
        print(f"🔄 Incremental Update: {len(deleted_tasks)} deleted, {len(new_fixed_tasks)} new fixed, {len(new_flexible_tasks)} new flexible")
        
        # ===== 1. 处理删除任务 =====
        if deleted_tasks:
            print("🗑️ Processing deleted tasks...")
            for window in self.windows:
                original_count = len(window["tasks"])
                window["tasks"] = [t for t in window["tasks"] if t["task_id"] not in deleted_ids]
                
                if len(window["tasks"]) < original_count:
                    affected_windows_for_rest.add(id(window))
                    updated_task_ids.extend([t["task_id"] for t in deleted_tasks])
        
        # ===== 2. 处理新增固定任务 =====
        if new_fixed_tasks:
            print("📌 Processing new fixed tasks...")
            try:
                earliest_fixed_time = min(
                    dt.datetime.strptime(t["start_time"], DATETIME_FORMAT) 
                    for t in new_fixed_tasks
                )
                
                tasks_to_reschedule = []
                windows_to_remove = []
                
                for window in self.windows:
                    if window["start_time"] >= earliest_fixed_time:
                        tasks_to_reschedule.extend(window["tasks"])
                        updated_task_ids.extend([t["task_id"] for t in window["tasks"]])
                        windows_to_remove.append(window)
                
                for window in windows_to_remove:
                    self.windows.remove(window)
                
                # 标准化新固定任务
                normalized_fixed = [self._normalize_task(t, is_fixed=True) if "_id" in t else t for t in new_fixed_tasks]
                
                self.timetable.extend(normalized_fixed)
                self.timetable.sort(key=lambda x: x["start_time"])
                
                new_windows = []
                for i in range(len(self.timetable) - 1):
                    try:
                        end_time = dt.datetime.strptime(self.timetable[i]["end_time"], DATETIME_FORMAT)
                        start_time = dt.datetime.strptime(self.timetable[i + 1]["start_time"], DATETIME_FORMAT)
                        
                        if start_time > end_time and end_time >= earliest_fixed_time:
                            new_windows.append({
                                "task_before": self.timetable[i],
                                "task_after":  self.timetable[i + 1],
                                "start_time":  end_time,
                                "end_time":    start_time,
                                "tasks":       []
                            })
                    except:
                        continue
                
                self.windows.extend(new_windows)
                self.windows.sort(key=lambda w: w["start_time"])
                
                # 重新分配被挤出的任务
                if tasks_to_reschedule:
                    print(f"  Rescheduling {len(tasks_to_reschedule)} displaced tasks...")
                    tasks_to_reschedule.sort(key=lambda x: (x["deadline"], -x["priority"], -x["duration"]))
                    
                    for task in tasks_to_reschedule:
                        task_id = task["task_id"]
                        duration = task["duration"]
                        deadline = dt.datetime.strptime(task["deadline"], DATETIME_FORMAT)
                        
                        scheduled = False
                        for window in self.windows:
                            if window["start_time"] >= deadline:
                                break
                            
                            window_duration = (window["end_time"] - window["start_time"]).total_seconds() / 60
                            used_duration = sum(t["duration"] for t in window["tasks"])
                            
                            if (used_duration + duration) * 1.25 <= window_duration:
                                window["tasks"].append(task)
                                affected_windows_for_reschedule.add(id(window))
                                scheduled = True
                                break
                        
                        if not scheduled:
                            self.unscheduled_tasks.append(task)
                            print(f"    ✗ Task {task_id} could not be rescheduled")
            except Exception as e:
                print(f"  Error processing fixed tasks: {e}")
        
        # ===== 3. 处理新增灵活任务 =====
        if new_flexible_tasks:
            print("📋 Processing new flexible tasks...")
            try:
                new_flexible_tasks.sort(key=lambda x: (x["deadline"], -x["priority"], -x["duration"]))
                
                earliest_new_deadline = dt.datetime.strptime(new_flexible_tasks[0]["deadline"], DATETIME_FORMAT)
                
                tasks_to_reschedule = []
                
                for window in self.windows:
                    if window["end_time"] >= earliest_new_deadline:
                        tasks_in_window = []
                        tasks_keep = []
                        
                        for task in window["tasks"]:
                            task_deadline = dt.datetime.strptime(task["deadline"], DATETIME_FORMAT)
                            if task_deadline >= earliest_new_deadline:
                                tasks_in_window.append(task)
                                updated_task_ids.append(task["task_id"])
                            else:
                                tasks_keep.append(task)
                        
                        tasks_to_reschedule.extend(tasks_in_window)
                        window["tasks"] = tasks_keep
                        
                        if tasks_in_window:
                            affected_windows_for_reschedule.add(id(window))
                
                tasks_to_reschedule.extend(new_flexible_tasks)
                tasks_to_reschedule.sort(key=lambda x: (x["deadline"], -x["priority"], -x["duration"]))
                
                print(f"  Arranging {len(tasks_to_reschedule)} tasks...")
                for task in tasks_to_reschedule:
                    task_id = task["task_id"]
                    duration = task["duration"]
                    deadline = dt.datetime.strptime(task["deadline"], DATETIME_FORMAT)
                    
                    scheduled = False
                    for window in self.windows:
                        if window["start_time"] >= deadline:
                            break
                        
                        window_duration = (window["end_time"] - window["start_time"]).total_seconds() / 60
                        used_duration = sum(t["duration"] for t in window["tasks"])
                        
                        if (used_duration + duration) * 1.25 <= window_duration:
                            window["tasks"].append(task)
                            affected_windows_for_reschedule.add(id(window))
                            scheduled = True
                            break
                    
                    if not scheduled:
                        self.unscheduled_tasks.append(task)
            except Exception as e:
                print(f"  Error processing flexible tasks: {e}")
        
        # ===== 4. 重新排序需要重排的窗口 =====
        print("⏱️ Re-ordering windows...")
        for window in self.windows:
            if id(window) in affected_windows_for_reschedule:
                tasks = window["tasks"]
                if len(tasks) <= 1:
                    continue
                
                task_before = _prepare_attributes(window["task_before"].copy())
                task_after = _prepare_attributes(window["task_after"].copy())
                tasks_within = [_prepare_attributes(t.copy()) for t in tasks]
                
                if len(tasks_within) <= 8:
                    best_score = float("inf")
                    best_perm = None
                    for perm in itertools.permutations(tasks_within):
                        candidate = [task_before] + list(perm) + [task_after]
                        score = _calculateScore(candidate, self.energy_weight)
                        if score < best_score:
                            best_score = score
                            best_perm = list(perm)
                    
                    if best_perm:
                        ordered_tasks = []
                        for prep_task in best_perm:
                            task_id = prep_task.get("task_id")
                            original = next((t for t in tasks if t["task_id"] == task_id), None)
                            if original:
                                ordered_tasks.append(original)
                        window["tasks"] = ordered_tasks
                else:
                    remaining = tasks_within[:]
                    sequence = [task_before]
                    while remaining:
                        best_next = None
                        best_score = float("inf")
                        for cand in remaining:
                            candidate = sequence + [cand] + [task_after]
                            score = _calculateScore(candidate, self.energy_weight)
                            if score < best_score:
                                best_score = score
                                best_next = cand
                        sequence.append(best_next)
                        remaining.remove(best_next)
                    
                    ordered_tasks = []
                    for prep_task in sequence[1:]:
                        task_id = prep_task.get("task_id")
                        original = next((t for t in tasks if t["task_id"] == task_id), None)
                        if original:
                            ordered_tasks.append(original)
                    window["tasks"] = ordered_tasks
                
                affected_windows_for_rest.add(id(window))
        
        # ===== 5. 重新分配休息时间 =====
        print("😴 Re-distributing rest times...")
        for window in self.windows:
            if id(window) in affected_windows_for_rest:
                tasks = window["tasks"]
                if not tasks:
                    continue
                
                total_task_duration = sum(t["duration"] for t in tasks)
                total_window_duration = (window["end_time"] - window["start_time"]).total_seconds() / 60.0
                rest_budget = total_window_duration - total_task_duration
                
                if rest_budget <= 0:
                    rest_start_time = window["start_time"]
                    for j in range(len(tasks)):
                        window["tasks"][j]["start_time"] = rest_start_time.strftime(DATETIME_FORMAT)
                        rest_start_time = dt.datetime.strptime(window["tasks"][j]["start_time"], DATETIME_FORMAT) + dt.timedelta(minutes=window["tasks"][j]["duration"])
                    continue
                
                slots_params = []
                for j in range(len(tasks) + 1):
                    i = min(j, len(tasks) - 1)
                    t = tasks[i]
                    
                    alpha_E = t.get("alpha_E", 1.0)
                    alpha_P = t.get("alpha_P", 1.0)
                    b = t.get("rest_slope_b", 0.08)
                    c = t.get("rest_center_c", 10.0)
                    C = self.energy_weight * alpha_E + (1 - self.energy_weight) * alpha_P
                    
                    slots_params.append({
                        "C": C, "b": b, "c": c,
                        "rmin": 0.0,
                        "rmax": t.get("rest_rmax", float("inf")),
                    })
                
                rests = _allocate_rest_sigmoid(rest_budget, slots_params, tol=1e-4, max_iter=80)
                
                rest_start_time = window["start_time"]
                for j in range(len(tasks)):
                    rest_minutes = rests[j] if j < len(rests) else 0
                    window["tasks"][j]["start_time"] = (rest_start_time + dt.timedelta(minutes=rest_minutes)).strftime(DATETIME_FORMAT)
                    rest_start_time = dt.datetime.strptime(window["tasks"][j]["start_time"], DATETIME_FORMAT) + dt.timedelta(minutes=window["tasks"][j]["duration"])
        
        # ===== 6. 返回更新结果 =====
        print("✅ Incremental update complete")
        return {
            "success": True,
            "windows": self._serialize_windows(self.windows),
            "unscheduled_tasks": self.unscheduled_tasks,
            "updated_task_ids": list(set(updated_task_ids)),
            "message": f"Schedule updated: {len(new_fixed_tasks)} fixed tasks, {len(new_flexible_tasks)} flexible tasks added"
        }

    def _serialize_windows(self, windows):
        """将窗口数据序列化为前端可用的格式"""
        serialized = []
        for window in windows:
            serialized.append({
                "window_id": id(window),
                "start_time": window["start_time"].strftime(DATETIME_FORMAT),
                "end_time": window["end_time"].strftime(DATETIME_FORMAT),
                "tasks": [
                    {
                        "task_id": t["task_id"],
                        "start_time": t.get("start_time", ""),
                        "duration": t.get("duration", 0),
                        "name": t.get("name", "")
                    }
                    for t in window["tasks"]
                ],
                "score": window.get("score")
            })
        return serialized
