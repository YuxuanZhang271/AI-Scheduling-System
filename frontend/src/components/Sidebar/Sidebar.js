import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Sidebar.css";

export default function Sidebar() {
  const [isOpen, setIsOpen] = useState(false);
  const [reportOpen, setReportOpen] = useState(false);
  const navigate = useNavigate();

  const username = localStorage.getItem("userEmail") || "User";

  return (
    <div
      className={`sidebar ${isOpen ? "open" : ""}`}
      onMouseEnter={() => setIsOpen(true)}
      onMouseLeave={() => setIsOpen(false)}
    >
      <div className="sidebar-header">
        {isOpen && <p className="welcome">Hello {username},</p>}
        <div className="menu-toggle">☰</div>
      </div>

      {isOpen && (
        <div className="sidebar-content">
          <h2 className="brand">AI-Powered Scheduling</h2>
          <p className="subtitle">
            Smart daily planning that adapts to your energy and priorities.
          </p>

          <ul className="menu-list">
            <li onClick={() => navigate("/schedule")}>
              <span className="icon">▦</span> Dashboard
            </li>
            <li onClick={() => navigate("/tasks")}>
              <span className="icon">📝</span> Today's Task
            </li>

            {/* Report 父菜单 */}
            <li onClick={() => setReportOpen(!reportOpen)}>
              <span className="icon">📑</span> Report {reportOpen ? "▲" : "▼"}
            </li>

            {/* 子菜单 */}
            {reportOpen && (
              <ul className="submenu">
                <li onClick={() => navigate("/report/daily")}>✔ Daily Report</li>
                <li onClick={() => navigate("/report/weekly")}>✔ Weekly Report</li>
              </ul>
            )}

            <li onClick={() => navigate("/chatbot")}>
              <span className="icon">💬</span> AI Chatbot
            </li>
            <li
              onClick={() => {
                localStorage.removeItem("authToken");
                localStorage.removeItem("userEmail");
                navigate("/login");
              }}
            >
              <span className="icon">🚪</span> Logout
            </li>
          </ul>
        </div>
      )}
    </div>
  );
}
