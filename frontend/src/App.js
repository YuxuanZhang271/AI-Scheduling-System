import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import Login from "./pages/Login";
import Schedule from "./pages/Schedule";
import TasksBoard from "./pages/TasksBoard";
import Report from "./pages/Report";
import DailyReport from "./pages/DailyReport";
import WeeklyReport from "./pages/WeeklyReport";
import Chatbot from "./pages/Chatbot";
import Sidebar from "./components/Sidebar/Sidebar";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("authToken");
    if (token) setIsAuthenticated(true);
  }, []);

  // ✅ 登录成功回调
  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  // ✅ 登出逻辑（新增）
  const handleLogout = () => {
    // 清空所有本地认证信息
    localStorage.removeItem("authToken");
    localStorage.removeItem("user_id");
    setIsAuthenticated(false);
    // 直接跳转到登录页
    window.location.href = "/login";
  };

  return (
    <Router>
      <div style={{ display: "flex", height: "100vh" }}>
        {isAuthenticated && <Sidebar onLogout={handleLogout} />} {/* ✅ 修改调用 */}
        <Routes>
          <Route path="/login" element={<Login onLogin={handleLogin} />} />
          <Route path="/schedule" element={isAuthenticated ? <Schedule /> : <Navigate to="/login" />} />
          <Route path="/tasks" element={isAuthenticated ? <TasksBoard /> : <Navigate to="/login" />} />
          <Route path="/report" element={isAuthenticated ? <Report /> : <Navigate to="/login" />} />
          <Route path="/daily" element={isAuthenticated ? <DailyReport /> : <Navigate to="/login" />} />
          <Route path="/weekly" element={isAuthenticated ? <WeeklyReport /> : <Navigate to="/login" />} />
          <Route path="/chatbot" element={isAuthenticated ? <Chatbot /> : <Navigate to="/login" />} />
          <Route path="*" element={<Navigate to={isAuthenticated ? "/schedule" : "/login"} />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
