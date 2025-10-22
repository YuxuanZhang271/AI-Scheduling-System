import React, { useState, useEffect, useCallback } from "react";
import { useLocation } from "react-router-dom";
import Calendar from "../components/Calendar/Calendar";
import AddTask from "../components/AddTask/AddTask";
import HeaderBar from "../components/HeaderBar/HeaderBar";
import { getTasks, createTask, deleteTask, updateTask } from "../services/api";

// 🧩 时间转换为小时
function fmtDuration(minutes) {
  if (!minutes) return "0 h";
  const hours = minutes / 60;
  if (hours >= 1) return `${hours.toFixed(1)} h`;
  return `${minutes} min`;
}

// ✅ 标准化 fixed 任务
function normalizeFixedTask(doc) {
  const rawDuration = doc.task_duration ?? doc.expected_duration ?? 60;
  const duration = rawDuration < 10 ? rawDuration : rawDuration / 60;
  return {
    id: doc._id || doc.id,
    name: doc.task_name ?? doc.name ?? "",
    startTime: doc.task_start_time || "",
    duration,
    category: doc.task_type ?? doc.category ?? "work",
    difficulty: doc.expected_difficulty ?? doc.difficulty ?? 3,
    location: doc.task_location ?? doc.location ?? "",
    status: doc.status ?? "assigned",
    mode: "fixed",
    priority: doc.task_priority ?? 1,
    predicted_energy: doc.predicted_energy ?? null,
    predicted_pressure: doc.predicted_pressure ?? null,
  };
}

// ✅ 标准化 flexible 任务
function normalizeFlexibleTask(doc) {
  const rawDuration = doc.expected_duration ?? doc.duration ?? 60;
  const duration = rawDuration < 10 ? rawDuration : rawDuration / 60;
  return {
    id: doc._id || doc.id,
    name: doc.task_name ?? doc.name ?? "",
    startTime: doc.start_time || "",
    deadline: doc.task_deadline ?? "",
    duration,
    category: doc.task_type ?? doc.category ?? "work",
    difficulty: doc.expected_difficulty ?? doc.difficulty ?? 3,
    priority: doc.task_priority ?? 1,
    status: doc.status ?? "unassigned",
    mode: "flexible",
    predicted_energy: doc.predicted_energy ?? null,
    predicted_pressure: doc.predicted_pressure ?? null,
  };
}

// ✅ 将 YYYYMMDDHHMM 转 datetime-local 格式
function convertTimeFormat(timeStr) {
  if (!timeStr || timeStr.length !== 12) return "";
  const y = timeStr.slice(0, 4);
  const m = timeStr.slice(4, 6);
  const d = timeStr.slice(6, 8);
  const hh = timeStr.slice(8, 10);
  const mm = timeStr.slice(10, 12);
  return `${y}-${m}-${d}T${hh}:${mm}:00`;
}

// ✅ 处理跨天任务（拆分）
function splitOvernightTask(task) {
  if (!task.startTime || !task.duration) return [task];

  const y = task.startTime.slice(0, 4);
  const m = task.startTime.slice(4, 6);
  const d = task.startTime.slice(6, 8);
  const hh = task.startTime.slice(8, 10);
  const mm = task.startTime.slice(10, 12);
  const start = new Date(`${y}-${m}-${d}T${hh}:${mm}:00`);

  const end = new Date(start.getTime() + task.duration * 60 * 60 * 1000);
  const diffDays = end.getDate() - start.getDate();

  // ✅ 如果没有跨天，直接返回
  if (diffDays === 0) return [task];

  // ✅ 跨天：拆成两段
  const firstDuration = (24 - start.getHours() - start.getMinutes() / 60);
  const secondDuration = task.duration - firstDuration;

  const nextDay = new Date(start);
  nextDay.setDate(nextDay.getDate() + 1);
  const nextY = nextDay.getFullYear();
  const nextM = String(nextDay.getMonth() + 1).padStart(2, "0");
  const nextD = String(nextDay.getDate()).padStart(2, "0");

  const nextStart = `${nextY}${nextM}${nextD}0000`;

  const firstPart = { ...task, duration: firstDuration };
  const secondPart = { ...task, startTime: nextStart, duration: secondDuration };

  return [firstPart, secondPart];
}

export default function Schedule({ refreshFlag }) {
  const [open, setOpen] = useState(false);
  const [tasks, setTasks] = useState([]);
  const [defaultTime, setDefaultTime] = useState("");
  const [editingTask, setEditingTask] = useState(null);
  const [time, setTime] = useState(new Date());
  const [energy, setEnergy] = useState(2);
  const [pressure, setPressure] = useState(3);
  const location = useLocation();

  const userId = localStorage.getItem("user_id");

  // 🕒 实时更新时钟
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  // ✅ 从数据库加载任务并自动处理跨天
  const fetchTasksFromDB = useCallback(async () => {
    if (!userId) return;
    try {
      console.log("🔄 Fetching tasks from DB for user:", userId);
      const res = await getTasks(`${userId}/all`);
      const fixedRaw = res?.data?.fixed || [];
      const flexibleRaw = res?.data?.flexible || [];

      const normalizedFixed = fixedRaw.map(normalizeFixedTask);
      const normalizedFlex = flexibleRaw.map(normalizeFlexibleTask);

      // ✅ 自动拆分跨天任务
      const expandedFixed = normalizedFixed.flatMap(splitOvernightTask);
      const expandedFlex = normalizedFlex.flatMap(splitOvernightTask);

      const combined = [...expandedFixed, ...expandedFlex];

      combined.sort((a, b) => (a.startTime || "").localeCompare(b.startTime || ""));
      setTasks(combined);
    } catch (err) {
      console.error("❌ Failed to fetch tasks:", err);
    }
  }, [userId]);

  // ✅ 初次加载 + Chatbot 刷新
  useEffect(() => {
    fetchTasksFromDB();
  }, [fetchTasksFromDB, refreshFlag]);

  // ✅ 页面重新获得焦点时刷新
  useEffect(() => {
    const onFocus = () => fetchTasksFromDB();
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [fetchTasksFromDB]);

  // ✅ 每分钟自动刷新
  useEffect(() => {
    const interval = setInterval(() => fetchTasksFromDB(), 60000);
    return () => clearInterval(interval);
  }, [fetchTasksFromDB]);

  // ✅ 创建或更新任务
  const handleConfirm = async (task) => {
    try {
      console.log("➕ Creating or updating task:", task);
      if (editingTask?.id) {
        const type = task.mode === "flexible" ? "flex" : "fixed";
        await updateTask(task.id, type, task);
      } else {
        await createTask(userId, task);
      }
      await fetchTasksFromDB();
    } catch (err) {
      console.error("❌ Failed to create task:", err);
    } finally {
      setOpen(false);
      setEditingTask(null);
    }
  };

  // ✅ 删除任务
  const handleDelete = async (id, mode) => {
    try {
      const type = mode === "fixed" ? "fixed" : "flex";
      await deleteTask(id, type);
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
          tasks={tasks}
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
}
