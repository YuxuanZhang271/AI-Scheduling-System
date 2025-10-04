import React, { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar/Sidebar";
import Calendar from "../components/Calendar/Calendar";
import AddTask from "../components/AddTask/AddTask";

export default function Schedule() {
  const [open, setOpen] = useState(false);
  const [tasks, setTasks] = useState([]);
  const [defaultTime, setDefaultTime] = useState("");
  const [editingTask, setEditingTask] = useState(null);
  const [time, setTime] = useState(new Date());

  // ⏰ 实时更新时间
  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (date) => {
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    return `${month}/${day} ${hours}:${minutes}`;
  };

  const handleConfirm = (task) => {
    if (editingTask) {
      setTasks((prev) =>
        prev.map((t) => (t.id === editingTask.id ? { ...task, id: editingTask.id } : t))
      );
      setEditingTask(null);
    } else {
      setTasks((prev) => [...prev, { ...task, id: Date.now() }]);
    }
  };

  const handleDelete = (taskId) => {
    setTasks((prev) => prev.filter((t) => t.id !== taskId));
    setEditingTask(null);
  };

  return (
    <div style={{ display: "flex", width: "100%" }}>
      <Sidebar />

      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        {/* 🔹 顶部栏（没有汉堡按钮） */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "white",
            borderBottom: "2px solid #9c27b0",
            padding: "8px 20px",
          }}
        >
          {/* 左边按钮区 */}
          <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
            <button
              onClick={() => setOpen(true)}
              style={{
                background: "orange",
                border: "none",
                padding: "10px 20px",
                borderRadius: "6px",
                color: "white",
                fontWeight: "bold",
                cursor: "pointer",
              }}
            >
              Add Task
            </button>

            <button
              style={{
                background: "orange",
                border: "none",
                padding: "10px 20px",
                borderRadius: "6px",
                color: "white",
                fontWeight: "bold",
                cursor: "pointer",
              }}
            >
              Record Conditions
            </button>
          </div>

          {/* 中间时间 */}
          <span style={{ fontSize: "18px", fontWeight: "bold", color: "#0d47a1" }}>
            {formatTime(time)}
          </span>

          {/* 右侧 Energy / Pressure */}
          <div style={{ display: "flex", gap: "20px", alignItems: "center" }}>
            <div>
              <span style={{ marginRight: "6px" }}>Current Energy:</span>
              {Array.from({ length: 5 }).map((_, i) => (
                <span
                  key={i}
                  style={{
                    display: "inline-block",
                    width: "10px",
                    height: "10px",
                    margin: "0 2px",
                    borderRadius: "50%",
                    background: i < 2 ? "#64b5f6" : "#e0e0e0",
                  }}
                />
              ))}
            </div>

            <div>
              <span style={{ marginRight: "6px" }}>Current Pressure:</span>
              {Array.from({ length: 5 }).map((_, i) => (
                <span
                  key={i}
                  style={{
                    display: "inline-block",
                    width: "10px",
                    height: "10px",
                    margin: "0 2px",
                    borderRadius: "50%",
                    background: i < 2 ? "#64b5f6" : "#e0e0e0",
                  }}
                />
              ))}
            </div>
          </div>
        </div>

        {/* 日历主体 */}
        <div style={{ flex: 1, padding: "20px" }}>
          <Calendar
            tasks={tasks}
            onAddTask={() => {
              setDefaultTime("");
              setEditingTask(null);
              setOpen(true);
            }}
            onCellClick={(time) => {
              setDefaultTime(time);
              setEditingTask(null);
              setOpen(true);
            }}
            onTaskClick={(task) => {
              setEditingTask(task);
              setOpen(true);
            }}
          />
        </div>

        {/* 弹窗 */}
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
    </div>
  );
}
