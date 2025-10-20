import React, { useState, useEffect, useCallback } from "react";
import { useLocation } from "react-router-dom";
import Calendar from "../components/Calendar/Calendar";
import AddTask from "../components/AddTask/AddTask";
import HeaderBar from "../components/HeaderBar/HeaderBar";
import { getTasks, createTask, deleteTask } from "../services/api";

<<<<<<< HEAD
// 时间转换为小时
function fmtDuration(minutes) {
  if (!minutes) return "0 h";
  const hours = minutes / 60;
  if (hours >= 1) {
    return `${hours.toFixed(1)} h`;
  }
  return `${minutes} min`;
}

// ✅ 修复：标准化 fixed 任务 - 确保时间格式正确
function normalizeFixedTask(doc) {
  console.log("📅 Normalizing fixed task:", doc);
  
  const rawDuration = doc.task_duration ?? doc.expected_duration ?? 60;
  let duration;
  
  // 如果持续时间小于10，认为是小时，否则认为是分钟
  if (rawDuration < 10) {
    duration = rawDuration; // 小时
  } else {
    duration = rawDuration / 60; // 分钟转小时
  }
  
  return {
    id: doc._id || doc.id,
    name: doc.task_name ?? doc.name ?? "",
    startTime: doc.task_start_time || "", // ✅ 保持 YYYYMMDDHHMM 格式
    duration: duration,
=======
// 将后端 fixed 文档映射为 Calendar 需要的前端结构
function normalizeFixedTask(doc) {
  return {
    id: doc._id || doc.id,
    name: doc.task_name ?? doc.name ?? "",
    startTime: doc.task_start_time ?? doc.startTime ?? "",
    duration:
      doc.task_duration ??
      doc.expected_duration ?? // 兜底
      1,
>>>>>>> 30116164397e8c1561c270e9510c582eea7af293
    category: doc.task_type ?? doc.category ?? "work",
    difficulty: doc.expected_difficulty ?? doc.difficulty ?? 3,
    location: doc.task_location ?? doc.location ?? "",
    status: doc.status ?? "assigned",
    mode: "fixed",
<<<<<<< HEAD
    priority: doc.task_priority ?? 1,
  };
}

// ✅ 修复：标准化灵活任务 - 确保时间格式正确
function normalizeFlexibleTask(doc) {
  console.log("🌀 Normalizing flexible task:", doc);
  
  const rawDuration = doc.expected_duration ?? doc.duration ?? 60;
  let duration;
  
  // 如果持续时间小于10，认为是小时，否则认为是分钟
  if (rawDuration < 10) {
    duration = rawDuration; // 小时
  } else {
    duration = rawDuration / 60; // 分钟转小时
  }
  
  return {
    id: doc._id || doc.id,
    name: doc.task_name ?? doc.name ?? "",
    startTime: doc.start_time || "", // ✅ 保持 YYYYMMDDHHMM 格式
    deadline: doc.task_deadline ?? "",
    duration: duration,
    category: doc.task_type ?? doc.category ?? "work",
    difficulty: doc.expected_difficulty ?? doc.difficulty ?? 3,
    priority: doc.task_priority ?? 1,
    status: doc.status ?? "unassigned",
    mode: "flexible",
  };
}

// ✅ 将 YYYYMMDDHHMM 格式转换为 datetime-local 字符串格式
function convertTimeFormat(timeStr) {
  if (!timeStr || timeStr.length !== 12) return "";
  try {
    const y = timeStr.slice(0, 4);
    const m = timeStr.slice(4, 6);
    const d = timeStr.slice(6, 8);
    const hh = timeStr.slice(8, 10);
    const mm = timeStr.slice(10, 12);
    return `${y}-${m}-${d}T${hh}:${mm}:00`;
  } catch {
    return "";
  }
}

export default function Schedule() {
  const [open, setOpen] = useState(false);
  const [tasks, setTasks] = useState([]);
=======
  };
}

export default function Schedule() {
  const [open, setOpen] = useState(false);
  const [tasks, setTasks] = useState([]); // 只存 fixed（已标准化）
>>>>>>> 30116164397e8c1561c270e9510c582eea7af293
  const [defaultTime, setDefaultTime] = useState("");
  const [editingTask, setEditingTask] = useState(null);
  const [time, setTime] = useState(new Date());
  const [energy, setEnergy] = useState(2);
  const [pressure, setPressure] = useState(3);
  const location = useLocation();

  const userId = localStorage.getItem("user_id");

<<<<<<< HEAD
  // 🕒 实时更新时钟
=======
  // 时钟（你原逻辑保留）
>>>>>>> 30116164397e8c1561c270e9510c582eea7af293
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

<<<<<<< HEAD
  // ✅ 从数据库读取所有任务并合并排序
  const fetchTasksFromDB = useCallback(async () => {
    if (!userId) return;
    try {
      console.log("🔄 Fetching tasks from DB for user:", userId);
      const res = await getTasks(userId);
      console.log("📦 Raw API response:", res);
      
      const fixedRaw = res?.data?.fixed || [];
      const flexibleRaw = res?.data?.flexible || [];
      
      console.log(`📊 Raw tasks - Fixed: ${fixedRaw.length}, Flexible: ${flexibleRaw.length}`);
      
      const normalized_fixed = fixedRaw.map(normalizeFixedTask);
      const normalized_flex = flexibleRaw.map(normalizeFlexibleTask);
      
      console.log("✅ Normalized fixed tasks:", normalized_fixed);
      console.log("✅ Normalized flexible tasks:", normalized_flex);
      
      // 合并并按时间排序
      const combined = [...normalized_fixed, ...normalized_flex];
      combined.sort((a, b) => {
        const timeA = a.startTime || "";
        const timeB = b.startTime || "";
        return timeA.localeCompare(timeB);
      });
      
      console.log("🎯 Final combined tasks for calendar:", combined);
      setTasks(combined);
    } catch (err) {
      console.error("❌ Failed to fetch tasks:", err);
    }
  }, [userId]);

=======
  // 从数据库读取并标准化 fixed 任务
  const fetchTasksFromDB = useCallback(async () => {
    if (!userId) return;
    try {
      const res = await getTasks(userId);
      const fixedRaw = (res?.data?.fixed ?? []);
      const normalized = fixedRaw.map(normalizeFixedTask);
      setTasks(normalized);
    } catch (err) {
      console.error("❌ Failed to fetch fixed tasks:", err);
    }
  }, [userId]);

  // 进入页面时：拉取数据库
>>>>>>> 30116164397e8c1561c270e9510c582eea7af293
  useEffect(() => {
    fetchTasksFromDB();
  }, [fetchTasksFromDB]);

<<<<<<< HEAD
  // ✅ 页面重新获得焦点时刷新
=======
  // 页面重新获得焦点（从别的页面切回 /schedule）：再次拉取数据库
>>>>>>> 30116164397e8c1561c270e9510c582eea7af293
  useEffect(() => {
    const onFocus = () => fetchTasksFromDB();
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [fetchTasksFromDB]);

<<<<<<< HEAD
  // 每分钟刷新一次
  useEffect(() => {
    const interval = setInterval(() => fetchTasksFromDB(), 60000);
    return () => clearInterval(interval);
  }, [fetchTasksFromDB]);

  // ✅ 添加任务
  const handleConfirm = async (task) => {
    try {
      console.log("➕ Creating task:", task);
      await createTask(userId, task);
      await fetchTasksFromDB();
=======
  // 创建任务：成功后不本地追加，直接重新拉取数据库，确保与 Calendar 字段一致
  const handleConfirm = async (task) => {
    try {
      await createTask(userId, task);
      await fetchTasksFromDB(); // ✅ 以数据库为准
>>>>>>> 30116164397e8c1561c270e9510c582eea7af293
    } catch (err) {
      console.error("❌ Failed to create task:", err);
    } finally {
      setOpen(false);
      setEditingTask(null);
    }
  };

<<<<<<< HEAD
  // ✅ 删除任务
  const handleDelete = async (id) => {
    try {
      console.log("🗑️ Deleting task:", id);
=======
  // 删除任务：成功后再拉取数据库
  const handleDelete = async (id) => {
    try {
>>>>>>> 30116164397e8c1561c270e9510c582eea7af293
      await deleteTask(id, "fixed");
      await fetchTasksFromDB();
    } catch (err) {
      console.error("❌ Failed to delete task:", err);
    }
  };

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
      <HeaderBar
        onAddTask={() => {
          setDefaultTime("");
          setEditingTask(null);
          setOpen(true);
        }}
        time={time}
        energy={energy}
        setEnergy={setEnergy}
        pressure={pressure}
        setPressure={setPressure}
      />

      <div style={{ flex: 1, padding: 20 }}>
        <Calendar
<<<<<<< HEAD
          tasks={tasks}
=======
          tasks={tasks} // ✅ 已标准化的 fixed 任务
>>>>>>> 30116164397e8c1561c270e9510c582eea7af293
          onAddTask={() => {
            setDefaultTime("");
            setEditingTask(null);
            setOpen(true);
          }}
          onCellClick={(timeStr) => {
            setDefaultTime(timeStr);
            setEditingTask(null);
            setOpen(true);
          }}
          onTaskClick={(task) => {
<<<<<<< HEAD
            console.log("📝 Editing task:", task);
=======
>>>>>>> 30116164397e8c1561c270e9510c582eea7af293
            setEditingTask(task);
            setOpen(true);
          }}
        />
      </div>

      <AddTask
        isOpen={open}
        onClose={() => setOpen(false)}
        onConfirm={handleConfirm}
        onDelete={handleDelete}
        defaultTime={defaultTime}
        editingTask={editingTask}
      />
    </div>
  );
<<<<<<< HEAD
}
=======
}
>>>>>>> 30116164397e8c1561c270e9510c582eea7af293
