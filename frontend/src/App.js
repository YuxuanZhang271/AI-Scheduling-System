<<<<<<< HEAD
import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Sidebar from "./components/Sidebar/Sidebar";
=======
import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
>>>>>>> 30116164397e8c1561c270e9510c582eea7af293
import Schedule from "./pages/Schedule";
import TasksBoard from "./pages/TasksBoard";
import Report from "./pages/Report";
import DailyReport from "./pages/DailyReport";
import WeeklyReport from "./pages/WeeklyReport";
import Chatbot from "./pages/Chatbot";
<<<<<<< HEAD
import Login from "./pages/Login";

function App() {
  const isLoggedIn = localStorage.getItem("access_token");
=======
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
>>>>>>> 30116164397e8c1561c270e9510c582eea7af293

  return (
    <Router>
      <div style={{ display: "flex", height: "100vh" }}>
<<<<<<< HEAD
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
=======
        {isAuthenticated && <Sidebar onLogout={() => setIsAuthenticated(false)} />} {/* 登录后显示侧边栏 */}

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
>>>>>>> 30116164397e8c1561c270e9510c582eea7af293
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
