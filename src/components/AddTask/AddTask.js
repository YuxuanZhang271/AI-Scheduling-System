import React, { useState, useEffect } from "react";
import "./AddTask.css";
import { createTask, updateTask } from "../services/api";  

export default function AddTask({
  isOpen,
  onClose,
  onConfirm,
  onDelete,
  defaultTime,
  editingTask,
}) {
  const initialTask = editingTask || {
    name: "",
    startTime: defaultTime || "",
    duration: 1,
    deadline: "",
    category: "",
    mode: "",
    priority: "",
    difficulty: "",
  };

  const [task, setTask] = useState(initialTask);

  useEffect(() => {
    setTask(initialTask);
  }, [editingTask, defaultTime]);

  const handleChange = (field, value) => {
    setTask((prev) => ({ ...prev, [field]: value }));
  };

  // 切換 mode 時清空不必要的欄位
  useEffect(() => {
    if (!task.mode) return;
    setTask((prev) =>
      prev.mode === "fixed"
        ? { ...prev, deadline: "" }
        : { ...prev, startTime: "" }
    );
  }, [task.mode]);

  const handleConfirmClick = async () => {
    if (!task.name) return;
    if (task.mode === "fixed" && !task.startTime) return;
    if (task.mode === "flexible" && !task.deadline) return;
    if (!task.mode) return;

    try {
      let saved;
      if (editingTask && editingTask.id) {
        // 編輯已有任務
        saved = await updateTask(editingTask.id, task);
      } else {
        // 新增任務
        saved = await createTask(task);
      }
      // 呼叫父層 onConfirm，傳回後端存好的那個任務物件（包含 id）
      onConfirm(saved);
      onClose();
    } catch (err) {
      console.error("Failed to save task:", err);
      // 你可以加個錯誤通報給使用者（alert 或 banner）
    }
  };

  // 拖曳（原本不變）
  useEffect(() => {
    if (!isOpen) return;
    const modal = document.querySelector(".task-modal");
    if (!modal) return;

    let offsetX = 0,
      offsetY = 0,
      isDragging = false;

    const header = modal.querySelector(".modal-header");

    const onMouseDown = (e) => {
      isDragging = true;
      offsetX = e.clientX - modal.getBoundingClientRect().left;
      offsetY = e.clientY - modal.getBoundingClientRect().top;
      document.addEventListener("mousemove", onMouseMove);
      document.addEventListener("mouseup", onMouseUp);
    };

    const onMouseMove = (e) => {
      if (!isDragging) return;
      modal.style.left = e.clientX - offsetX + "px";
      modal.style.top = e.clientY - offsetY + "px";
      modal.style.position = "absolute";
    };

    const onMouseUp = () => {
      isDragging = false;
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };

    header.addEventListener("mousedown", onMouseDown);
    return () => {
      header.removeEventListener("mousedown", onMouseDown);
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const categoryColors = {
    work: "#ffcc80",
    rest: "#81c784",
    fun: "#64b5f6",
    food: "#f48fb1",
  };

  return (
    <div className="task-modal-overlay">
      <div className="task-modal" lang="en">
        {/* Header */}
        <div className="modal-header">
          <h2 className="modal-title">
            {editingTask ? "Edit Task" : "Add Task"}
          </h2>
          <button className="close-btn" onClick={onClose}>
            ×
          </button>
        </div>

        {/* Task Name */}
        <input
          type="text"
          className="input-field"
          placeholder="Task Name"
          value={task.name}
          onChange={(e) => handleChange("name", e.target.value)}
        />

        {/* Mode */}
        <div className="section-title">Scheduling Mode</div>
        <div className="option-group">
          <div className="option">
            <label>Mode</label>
            <select
              className="inline-input"
              value={task.mode}
              onChange={(e) => handleChange("mode", e.target.value)}
            >
              <option value="">Select</option>
              <option value="fixed">Fixed</option>
              <option value="flexible">Flexible</option>
            </select>
          </div>
        </div>

        {/* Time */}
        <div className="section-title">Task Time</div>
        <div className="option-group">
          {task.mode === "fixed" && (
            <div className="option">
              <label>Start</label>
              <input
                type="datetime-local"
                className="inline-input time-input"
                lang="en"
                value={task.startTime}
                onChange={(e) => handleChange("startTime", e.target.value)}
              />
            </div>
          )}

          {task.mode === "flexible" && (
            <div className="option">
              <label>Deadline</label>
              <input
                type="datetime-local"
                className="inline-input time-input"
                lang="en"
                value={task.deadline}
                onChange={(e) => handleChange("deadline", e.target.value)}
              />
            </div>
          )}

          <div className="option">
            <label>Duration</label>
            <input
              type="number"
              className="inline-input"
              value={task.duration}
              onChange={(e) => handleChange("duration", e.target.value)}
              min="1"
              max="24"
            />
          </div>
        </div>

        {/* Settings */}
        <div className="section-title">Task Settings</div>
        <div className="option-group">
          <div className="option">
            <label>Category</label>
            <select
              className="inline-input"
              value={task.category}
              onChange={(e) => handleChange("category", e.target.value)}
              style={{
                background: categoryColors[task.category] || "#e0e0e0",
              }}
            >
              <option value="">Select</option>
              <option value="work">Work</option>
              <option value="rest">Rest</option>
              <option value="fun">Fun</option>
              <option value="food">Food</option>
            </select>
          </div>

          <div className="option">
            <label>Priority</label>
            <select
              className="inline-input"
              value={task.priority}
              onChange={(e) => handleChange("priority", e.target.value)}
            >
              <option value="">Select</option>
              <option value="1">1 (Low)</option>
              <option value="2">2 (Medium)</option>
              <option value="3">3 (High)</option>
            </select>
          </div>

          <div className="option">
            <label>Difficulty</label>
            <select
              className="inline-input"
              value={task.difficulty}
              onChange={(e) => handleChange("difficulty", e.target.value)}
            >
              <option value="">Select</option>
              <option value="1">1 (Easy)</option>
              <option value="2">2</option>
              <option value="3">3 (Normal)</option>
              <option value="4">4</option>
              <option value="5">5 (Hard)</option>
            </select>
          </div>
        </div>

        {/* Buttons */}
        <div style={{ display: "flex", gap: "10px" }}>
          <button className="confirm-btn" onClick={handleConfirmClick}>
            {editingTask ? "Save" : "Confirm"}
          </button>
          {editingTask && (
            <button
              className="confirm-btn"
              style={{ background: "red" }}
              onClick={() => onDelete(task.id)}
            >
              Delete
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
