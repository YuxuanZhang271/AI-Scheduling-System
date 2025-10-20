import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Sidebar from "./components/Sidebar/Sidebar";
import Schedule from "./pages/Schedule";
import TasksBoard from "./pages/TasksBoard";
import Report from "./pages/Report";
import DailyReport from "./pages/DailyReport";
import WeeklyReport from "./pages/WeeklyReport";
import Chatbot from "./pages/Chatbot";
import Login from "./pages/Login";

function App() {
  const isLoggedIn = localStorage.getItem("access_token");

  return (
    <Router>
      <div style={{ display: "flex", height: "100vh" }}>
        {isLoggedIn && <Sidebar />}
        <div style={{ flex: 1, overflowY: "auto" }}>
          <Routes>
            {/* 默认跳转到登录或日程 */}
            <Route path="/" element={<Navigate to={isLoggedIn ? "/schedule" : "/login"} />} />
            <Route path="/login" element={<Login />} />

            {/* 各个独立页面 */}
            <Route path="/schedule" element={<Schedule />} />
            <Route path="/tasks" element={<TasksBoard />} />
            <Route path="/report" element={<Report />} />
            <Route path="/report/daily" element={<DailyReport />} />
            <Route path="/report/weekly" element={<WeeklyReport />} />
            <Route path="/chatbot" element={<Chatbot />} />

            {/* 未匹配的路径 */}
            <Route path="*" element={<Navigate to="/schedule" />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
