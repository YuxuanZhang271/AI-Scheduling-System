import React, { useState, useEffect } from "react";
import Calendar from "../components/Calendar/Calendar";
import AddTask from "../components/AddTask/AddTask";
import HeaderBar from "../components/HeaderBar/HeaderBar";

export default function Schedule() {
  const [open, setOpen] = useState(false);
  const [tasks, setTasks] = useState([]);
  const [defaultTime, setDefaultTime] = useState("");
  const [editingTask, setEditingTask] = useState(null);

  const [time, setTime] = useState(new Date());
  const [energy, setEnergy] = useState(2);
  const [pressure, setPressure] = useState(3);

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

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
