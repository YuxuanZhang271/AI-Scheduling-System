import React, { useState, useEffect, useCallback } from "react";
import { useLocation } from "react-router-dom";
import Calendar from "../components/Calendar/Calendar";
import AddTask from "../components/AddTask/AddTask";
import HeaderBar from "../components/HeaderBar/HeaderBar";
import { getTasks, createTask, deleteTask } from "../services/api";

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
    category: doc.task_type ?? doc.category ?? "work",
    difficulty: doc.expected_difficulty ?? doc.difficulty ?? 3,
    location: doc.task_location ?? doc.location ?? "",
    status: doc.status ?? "assigned",
    mode: "fixed",
  };
}

export default function Schedule() {
  const [open, setOpen] = useState(false);
  const [tasks, setTasks] = useState([]); // 只存 fixed（已标准化）
  const [defaultTime, setDefaultTime] = useState("");
  const [editingTask, setEditingTask] = useState(null);
  const [time, setTime] = useState(new Date());
  const [energy, setEnergy] = useState(2);
  const [pressure, setPressure] = useState(3);
  const location = useLocation();

  const userId = localStorage.getItem("user_id");

  // 时钟（你原逻辑保留）
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

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
  useEffect(() => {
    fetchTasksFromDB();
  }, [fetchTasksFromDB]);

  // 页面重新获得焦点（从别的页面切回 /schedule）：再次拉取数据库
  useEffect(() => {
    const onFocus = () => fetchTasksFromDB();
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [fetchTasksFromDB]);

  // 创建任务：成功后不本地追加，直接重新拉取数据库，确保与 Calendar 字段一致
  const handleConfirm = async (task) => {
    try {
      await createTask(userId, task);
      await fetchTasksFromDB(); // ✅ 以数据库为准
    } catch (err) {
      console.error("❌ Failed to create task:", err);
    } finally {
      setOpen(false);
      setEditingTask(null);
    }
  };

  // 删除任务：成功后再拉取数据库
  const handleDelete = async (id) => {
    try {
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
          tasks={tasks} // ✅ 已标准化的 fixed 任务
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
