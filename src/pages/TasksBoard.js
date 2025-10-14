import React, { useState, useEffect } from "react";
import HeaderBar from "../components/HeaderBar/HeaderBar";
import AddTask from "../components/AddTask/AddTask";

export default function TasksBoard() {
  const columns = ["Unassigned", "Assigned", "Processing", "Completed"];

  // 顶栏状态
  const [time, setTime] = useState(new Date());
  const [energy, setEnergy] = useState(2);
  const [pressure, setPressure] = useState(3);

  // AddTask 弹窗状态
  const [open, setOpen] = useState(false);
  const [tasks, setTasks] = useState([]);
  const [editingTask, setEditingTask] = useState(null);
  const [defaultTime, setDefaultTime] = useState("");

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // 保存任务
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

  // 删除任务
  const handleDelete = (taskId) => {
    setTasks((prev) => prev.filter((t) => t.id !== taskId));
    setEditingTask(null);
  };

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
      {/* ✅ 顶栏 */}
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

      {/* 任务看板主体 */}
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
              {/* 以后这里放任务卡片 */}
            </div>
          ))}
        </div>
      </div>

      {/* ✅ AddTask 弹窗 */}
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
