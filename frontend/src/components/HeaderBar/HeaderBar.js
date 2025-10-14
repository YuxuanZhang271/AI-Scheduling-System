import React, { useState } from "react";

export default function HeaderBar({ onAddTask, time, energy, setEnergy, pressure, setPressure }) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const formatTime = (date) => {
    const mm = String(date.getMonth() + 1).padStart(2, "0");
    const dd = String(date.getDate()).padStart(2, "0");
    const hh = String(date.getHours()).padStart(2, "0");
    const mi = String(date.getMinutes()).padStart(2, "0");
    return `${mm}/${dd} ${hh}:${mi}`;
  };

  return (
    <div style={{ display: "flex", flexDirection: "column" }}>
      {/* 顶栏 */}
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
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <button
            onClick={onAddTask}
            style={{ background: "orange", border: "none", padding: "10px 20px", borderRadius: 6, color: "#fff", fontWeight: "bold", cursor: "pointer" }}
          >Add Task</button>

          <button
            onClick={() => setIsModalOpen(true)}
            style={{ background: "orange", border: "none", padding: "10px 20px", borderRadius: 6, color: "#fff", fontWeight: "bold", cursor: "pointer" }}
          >Record Conditions</button>
        </div>

        <span style={{ fontSize: 18, fontWeight: "bold", color: "#0d47a1" }}>{formatTime(time)}</span>

        <div style={{ display: "flex", gap: 20, alignItems: "center" }}>
          <div>
            <span style={{ marginRight: 6 }}>Current Energy:</span>
            {Array.from({ length: 5 }).map((_, i) => (
              <span key={i} style={{ display: "inline-block", width: 10, height: 10, margin: "0 2px", borderRadius: "50%", background: i < energy ? "#64b5f6" : "#e0e0e0" }} />
            ))}
          </div>
          <div>
            <span style={{ marginRight: 6 }}>Current Pressure:</span>
            {Array.from({ length: 5 }).map((_, i) => (
              <span key={i} style={{ display: "inline-block", width: 10, height: 10, margin: "0 2px", borderRadius: "50%", background: i < pressure ? "#64b5f6" : "#e0e0e0" }} />
            ))}
          </div>
        </div>
      </div>

      {/* 条件记录弹窗 */}
      {isModalOpen && (
        <div
          style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.3)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}
          onClick={() => setIsModalOpen(false)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{ background: "#fff", padding: 20, borderRadius: 12, boxShadow: "0 4px 12px rgba(0,0,0,0.2)", width: 320 }}
          >
            <h3 style={{ marginBottom: 16, color: "#0d47a1" }}>Record Conditions</h3>

            <label style={{ display: "block", marginBottom: 8, fontWeight: 700, color: "#0d47a1" }}>Energy</label>
            <select
              value={energy}
              onChange={(e) => setEnergy(Number(e.target.value))}
              style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid #ccc", background: "#f9f9f9", marginBottom: 16 }}
            >
              {[1,2,3,4,5].map(n => <option key={n} value={n}>{n}</option>)}
            </select>

            <label style={{ display: "block", marginBottom: 8, fontWeight: 700, color: "#0d47a1" }}>Pressure</label>
            <select
              value={pressure}
              onChange={(e) => setPressure(Number(e.target.value))}
              style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid #ccc", background: "#f9f9f9", marginBottom: 20 }}
            >
              {[1,2,3,4,5].map(n => <option key={n} value={n}>{n}</option>)}
            </select>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
              <button onClick={() => setIsModalOpen(false)} style={{ background: "#ccc", border: "none", padding: "8px 16px", borderRadius: 6, cursor: "pointer" }}>Cancel</button>
              <button onClick={() => setIsModalOpen(false)} style={{ background: "orange", border: "none", padding: "8px 16px", borderRadius: 6, color: "#fff", fontWeight: "bold", cursor: "pointer" }}>Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
