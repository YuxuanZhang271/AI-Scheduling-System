import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
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

  // ✅ 启动时检测 localStorage 里是否有 token
  useEffect(() => {
    const token = localStorage.getItem("authToken");
    if (token) setIsAuthenticated(true);
  }, []);

  // ✅ 登录回调函数（Login 成功后调用）
  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  return (
    <Router>
      <div style={{ display: "flex", height: "100vh" }}>
        {isAuthenticated && <Sidebar />} {/* 登录后显示侧边栏 */}

        <div style={{ flex: 1, overflowY: "auto" }}>
          <Routes>
            {/* 默认路由 */}
            <Route
              path="/"
              element={
                isAuthenticated ? (
                  <Navigate to="/schedule" />
                ) : (
                  <Login onLogin={handleLogin} />
                )
              }
            />

            {/* 登录后路由 */}
            {isAuthenticated ? (
              <>
                <Route path="/schedule" element={<Schedule />} />
                <Route path="/tasks" element={<TasksBoard />} />
                <Route path="/chatbot" element={<Chatbot />} />
                <Route path="/report" element={<Report />}>
                  <Route index element={<Navigate to="/report/daily" />} />
                  <Route path="daily" element={<DailyReport />} />
                  <Route path="weekly" element={<WeeklyReport />} />
                </Route>
              </>
            ) : (
              <Route path="*" element={<Navigate to="/" />} />
            )}
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
