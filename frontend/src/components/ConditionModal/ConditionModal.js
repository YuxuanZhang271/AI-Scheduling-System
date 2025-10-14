import React from "react";

export default function ConditionModal({ isOpen, energy, pressure, onEnergyChange, onPressureChange, onClose }) {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100vw",
        height: "100vh",
        background: "rgba(0,0,0,0.3)",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 1000,
      }}
    >
      <div
        style={{
          background: "white",
          padding: "25px 30px",
          borderRadius: "12px",
          minWidth: "320px",
          boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
          fontFamily: "Arial, sans-serif",
        }}
      >
        <h3 style={{ marginBottom: "20px", color: "#0d47a1" }}>Record Conditions</h3>

        <div style={{ marginBottom: "18px" }}>
          <label style={{ display: "block", marginBottom: "6px", fontWeight: "bold", color: "#0d47a1" }}>
            Energy
          </label>
          <select
            value={energy}
            onChange={(e) => onEnergyChange(Number(e.target.value))}
            style={{
              width: "100%",
              padding: "10px",
              borderRadius: "8px",
              border: "1px solid #ccc",
              fontSize: "14px",
              outline: "none",
              appearance: "none",
              backgroundColor: "#f9f9f9",
              cursor: "pointer",
            }}
          >
            {[1, 2, 3, 4, 5].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>

        <div style={{ marginBottom: "20px" }}>
          <label style={{ display: "block", marginBottom: "6px", fontWeight: "bold", color: "#0d47a1" }}>
            Pressure
          </label>
          <select
            value={pressure}
            onChange={(e) => onPressureChange(Number(e.target.value))}
            style={{
              width: "100%",
              padding: "10px",
              borderRadius: "8px",
              border: "1px solid #ccc",
              fontSize: "14px",
              outline: "none",
              appearance: "none",
              backgroundColor: "#f9f9f9",
              cursor: "pointer",
            }}
          >
            {[1, 2, 3, 4, 5].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
          <button
            onClick={onClose}
            style={{
              background: "#ccc",
              color: "black",
              padding: "8px 16px",
              border: "none",
              borderRadius: "6px",
              cursor: "pointer",
              fontWeight: "bold",
            }}
          >
            Cancel
          </button>
          <button
            onClick={onClose}
            style={{
              background: "orange",
              color: "white",
              padding: "8px 16px",
              border: "none",
              borderRadius: "6px",
              cursor: "pointer",
              fontWeight: "bold",
            }}
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
