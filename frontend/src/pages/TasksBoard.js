import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import HeaderBar from "../components/HeaderBar/HeaderBar";
import AddTask from "../components/AddTask/AddTask";
import { getTasks, createTask, deleteTask } from "../services/api";

export default function TasksBoard() {
  const columns = ["Unassigned", "Assigned", "Processing", "Completed"];
  const [tasks, setTasks] = useState([]);
  const [open, setOpen] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [defaultTime, setDefaultTime] = useState("");
  const [time, setTime] = useState(new Date());
  const [energy, setEnergy] = useState(2);
  const [pressure, setPressure] = useState(3);
  const location = useLocation();

  const userId = localStorage.getItem("user_id");

  // 🕒 实时时钟
  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // 📦 加载灵活任务
  const fetchTasks = async () => {
    if (!userId) return;
    try {
      const res = await getTasks(userId);
      if (res && res.data) setTasks(res.data.flexible || []);
    } catch (err) {
      console.error("❌ Failed to load flexible tasks:", err);
    }
  };

  // ✅ 页面首次加载
  useEffect(() => {
    fetchTasks();
  }, [userId]);

  // ✅ 页面重新获得焦点时刷新
  useEffect(() => {
    const onFocus = () => fetchTasks();
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [userId]);

  // ✅ 添加任务
  const handleConfirm = async (task) => {
    try {
      const res = await createTask(userId, task);
      if (task.mode === "flexible") {
        setTasks((prev) => [...prev, { ...task, id: res.data.task_id }]);
      }
    } catch (err) {
      console.error("❌ Failed to add flexible task:", err);
    } finally {
      setOpen(false);
      setEditingTask(null);
    }
  };

  // ✅ 删除任务
  const handleDelete = async (id) => {
    try {
      await deleteTask(id, "flex");
      setTasks((prev) => prev.filter((t) => t.id !== id && t._id !== id));
    } catch (err) {
      console.error("❌ Failed to delete flexible task:", err);
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

      <div style={{ flex: 1, padding: "20px" }}>
        <div style={{ display: "flex", gap: "20px", height: "100%" }}>
          {columns.map((col) => (
            <div
              key={col}
              style={{
                flex: 1,
                background: "#f9f6f6",
                border: "1px solid #eee",
                borderRadius: "8px",
                padding: "10px",
              }}
            >
              <h3 style={{ textAlign: "center" }}>{col}</h3>
              {col === "Unassigned" &&
                tasks.map((t) => (
                  <div
                    key={t.id || t._id}
                    style={{
                      background: "#fff",
                      padding: "8px",
                      borderRadius: "6px",
                      marginBottom: "6px",
                      boxShadow: "0 1px 4px rgba(0,0,0,0.1)",
                      cursor: "pointer",
                    }}
                    onClick={() => {
                      setEditingTask(t);
                      setOpen(true);
                    }}
                  >
                    {t.task_name || t.name}
                  </div>
                ))}
            </div>
          ))}
        </div>
      </div>

      <AddTask
        isOpen={open}
        onClose={() => {
          setOpen(false);
          setEditingTask(null);
        }}
        onConfirm={handleConfirm}
        onDelete={handleDelete}
        defaultTime={defaultTime}
        editingTask={editingTask}
      />
    </div>
  );
}
