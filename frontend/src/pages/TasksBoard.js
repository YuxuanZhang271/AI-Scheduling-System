import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import HeaderBar from "../components/HeaderBar/HeaderBar";
import AddTask from "../components/AddTask/AddTask";
import {
  getTasks,
  createTask,
  deleteTask,
  updateTask,
  updateTaskStatus,
  runScheduler,
} from "../services/api";

function fmtTime(s) {
  if (!s) return "";
  try {
    if (/^\d{12}$/.test(s)) {
      const y = s.slice(0, 4),
        m = s.slice(4, 6),
        d = s.slice(6, 8),
        hh = s.slice(8, 10),
        mm = s.slice(10, 12);
      const dt = new Date(`${y}-${m}-${d}T${hh}:${mm}:00`);
      return dt.toLocaleString([], {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    }
    const d = new Date(s);
    return d.toLocaleString([], {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return String(s);
  }
}

// ✅ 修改这里：始终按小时显示
function fmtDuration(value) {
  if (!value) return "0 h";
  // 如果传入是分钟数（>=10），转小时；否则直接按小时
  const hours = value >= 10 ? value / 60 : value;
  return `${hours.toFixed(1)} h`;
}

function normalizeTask(doc, modeHint) {
  const mode =
    modeHint || (doc.task_start_time !== undefined ? "fixed" : "flexible");
  const id = doc._id || doc.id;
  const status =
    doc.status || (mode === "fixed" ? "assigned" : "unassigned");
  return {
    id,
    mode,
    name: doc.task_name || doc.name || "",
    category: doc.task_type || doc.category || "work",
    status,
    start_time:
      doc.task_start_time || doc.start_time || "",
    end_time: doc.end_time || "",
    duration:
      doc.task_duration || doc.expected_duration || doc.duration || 0,
    deadline: doc.task_deadline || doc.deadline || "",
  };
}

const nextStatusMap = {
  unassigned: "assigned",
  assigned: "processing",
  processing: "completed",
};

export default function TasksBoard() {
  const columns = ["Unassigned", "Assigned", "Processing", "Completed"];
  const [tasks, setTasks] = useState([]);
  const [open, setOpen] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [defaultTime, setDefaultTime] = useState("");
  const [time, setTime] = useState(new Date());
  const [energy, setEnergy] = useState(2);
  const [pressure, setPressure] = useState(3);
  const [flashIds, setFlashIds] = useState([]);
  const [loading, setLoading] = useState(false);
  const location = useLocation();
  const userId = localStorage.getItem("user_id");

  // 实时时钟
  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // 获取任务
  const fetchTasks = async () => {
    if (!userId) return;
    try {
      const res = await getTasks(userId);
      const fixedRaw = res?.data?.fixed || [];
      const flexRaw = res?.data?.flexible || [];
      const fixed = fixedRaw.map((d) => normalizeTask(d, "fixed"));
      const flex = flexRaw.map((d) => normalizeTask(d, "flexible"));
      setTasks((prev) => {
        const changed = [];
        const newMap = {};
        [...fixed, ...flex].forEach((t) => {
          newMap[t.id] = t;
          const old = prev.find((p) => p.id === t.id);
          if (old && old.status !== t.status) changed.push(t.id);
        });
        if (changed.length > 0) {
          setFlashIds(changed);
          setTimeout(() => setFlashIds([]), 2000);
        }
        return [...fixed, ...flex];
      });
    } catch (err) {
      console.error("❌ Failed to load tasks:", err);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, [userId]);

  useEffect(() => {
    const onFocus = () => fetchTasks();
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [userId]);

  useEffect(() => {
    const interval = setInterval(() => {
      fetchTasks();
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleConfirm = async (task) => {
  try {
    if (editingTask?.id) {
      // ✅ 编辑模式：更新任务
      const type = task.mode === "flexible" ? "flex" : "fixed";
      await updateTask(editingTask.id, type, task);
    } else {
      // ✅ 新建模式：创建任务
      await createTask(userId, task);
    }
    await fetchTasks();
  } catch (err) {
    console.error("❌ Failed to add/update task:", err);
  } finally {
    setOpen(false);
    setEditingTask(null);
  }
};


  const handleDelete = async (id, type) => {
    try {
      await deleteTask(id, type === "fixed" ? "fixed" : "flex");
      await fetchTasks();
    } catch (err) {
      console.error("❌ Failed to delete task:", err);
    }
  };

  const handleStatusChange = async (t, next) => {
    try {
      await updateTaskStatus(t.id, next);
      console.log(`✅ Task ${t.name} status updated to ${next}`);
      setTimeout(() => fetchTasks(), 300);
    } catch (err) {
      console.error("❌ Failed to update status:", err);
    }
  };

  const handleRunScheduler = async () => {
    if (loading) return;
    setLoading(true);
    try {
      console.log("🚀 Running scheduler...");
      const res = await runScheduler(userId);
      console.log("✅ Scheduler response:", res.data);
      setTimeout(() => {
        fetchTasks();
      }, 500);
      alert("✅ Intelligent scheduler executed!");
    } catch (err) {
      console.error("❌ Scheduler failed:", err);
      alert("❌ Scheduler failed, please check backend logs.");
    } finally {
      setLoading(false);
    }
  };

  const grouped = {
    Unassigned: tasks.filter((t) => t.status === "unassigned"),
    Assigned: tasks.filter((t) => t.status === "assigned"),
    Processing: tasks.filter((t) => t.status === "processing"),
    Completed: tasks.filter((t) => t.status === "completed"),
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

      <div style={{ display: "flex", justifyContent: "flex-end", padding: "10px 20px" }}>
        <button
          onClick={handleRunScheduler}
          disabled={loading}
          style={{
            background: loading ? "#999" : "#10b981",
            color: "#fff",
            border: "none",
            borderRadius: 8,
            padding: "8px 12px",
            fontWeight: 600,
            cursor: loading ? "not-allowed" : "pointer",
            opacity: loading ? 0.6 : 1,
            transition: "all 0.3s",
          }}
        >
          {loading ? "⏳ Running..." : "⚙️ Run Intelligent Scheduler"}
        </button>
      </div>

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
                overflow: "auto",
              }}
            >
              <h3 style={{ textAlign: "center", marginBottom: "12px" }}>
                {col}
                <span style={{ fontSize: "12px", color: "#999" }}>
                  {" "}({(grouped[col] || []).length})
                </span>
              </h3>

              {(grouped[col] || []).map((t) => (
                <div
                  key={t.id}
                  style={{
                    background: "#fff",
                    padding: "10px",
                    borderRadius: "10px",
                    marginBottom: "8px",
                    boxShadow: flashIds.includes(t.id)
                      ? "0 0 10px 2px #3b82f6"
                      : "0 2px 6px rgba(0,0,0,0.08)",
                    transition: "all 0.4s ease",
                    cursor: "pointer",
                  }}
                  onClick={() => {
                    setEditingTask(t.mode === "fixed" ? null : t);
                    if (t.mode !== "fixed") setOpen(true);
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <strong style={{ fontSize: 15 }}>{t.name}</strong>
                      <div style={{ fontSize: 12, color: "#666", marginTop: 4 }}>
                        {t.mode === "fixed" ? "📅 Fixed Task" : "🌀 Flexible"}
                      </div>
                      <div style={{ fontSize: 12, color: "#888", marginTop: 4 }}>
                        {t.mode === "fixed" ? (
                          <>
                            ⏰ {fmtTime(t.start_time)}{" "}
                            {t.duration ? `(${fmtDuration(t.duration)})` : ""}
                          </>
                        ) : t.start_time ? (
                          <>
                            🧩 Scheduled: {fmtTime(t.start_time)}
                            {t.duration ? ` (${fmtDuration(t.duration)})` : ""}
                          </>
                        ) : t.deadline ? (
                          <>📆 Deadline: {fmtTime(t.deadline)}</>
                        ) : null}
                      </div>
                    </div>

                    <div style={{ display: "flex", gap: 6, marginLeft: 8 }}>
                      {t.mode === "flexible" && nextStatusMap[t.status] && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStatusChange(t, nextStatusMap[t.status]);
                          }}
                          style={{
                            background: "#3b82f6",
                            color: "#fff",
                            border: "none",
                            borderRadius: 6,
                            padding: "4px 8px",
                            cursor: "pointer",
                            fontSize: 12,
                            whiteSpace: "nowrap",
                          }}
                        >
                          ↗ {nextStatusMap[t.status]}
                        </button>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(t.id, t.mode);
                        }}
                        style={{
                          background: "#ef4444",
                          color: "#fff",
                          border: "none",
                          borderRadius: 6,
                          padding: "4px 8px",
                          cursor: "pointer",
                          fontSize: 12,
                        }}
                      >
                        🗑
                      </button>
                    </div>
                  </div>
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
        onDelete={(id) => handleDelete(id, "flex")}
        defaultTime={defaultTime}
        editingTask={editingTask}
      />
    </div>
  );
}
