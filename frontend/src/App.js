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

  useEffect(() => {
    // ✅ 修正：統一使用 "access_token" 來檢查登入狀態
    const token = localStorage.getItem("access_token");
    if (token) {
      setIsAuthenticated(true);
    }
  }, []);

  // 登入成功後的回調函式
  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  // 登出邏輯
  const handleLogout = () => {
    // ✅ 修正：統一移除 "access_token"
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_id");
    setIsAuthenticated(false);
    window.location.href = "/login";
  };

  return (
    <Router>
      <div style={{ display: "flex", height: "100vh" }}>
        {isAuthenticated && <Sidebar onLogout={handleLogout} />}

        <div style={{ flex: 1, overflowY: "auto", background: "#f0f2f5" }}>
          <Routes>
            <Route path="/login" element={<Login onLogin={handleLogin} />} />
            
            <Route path="/schedule" element={<ProtectedRoute isAuthenticated={isAuthenticated}><Schedule /></ProtectedRoute>} />
            <Route path="/tasks" element={<ProtectedRoute isAuthenticated={isAuthenticated}><TasksBoard /></ProtectedRoute>} />
            <Route path="/chatbot" element={<ProtectedRoute isAuthenticated={isAuthenticated}><Chatbot /></ProtectedRoute>} />

            <Route 
              path="/report" 
              element={<ProtectedRoute isAuthenticated={isAuthenticated}><Report /></ProtectedRoute>}
            >
              <Route index element={<Navigate to="daily" replace />} />
              <Route path="daily" element={<DailyReport />} />
              <Route path="weekly" element={<WeeklyReport />} />
            </Route>

            <Route 
              path="*" 
              element={<Navigate to={isAuthenticated ? "/schedule" : "/login"} />} 
            />
          </Routes>
        </div>

      </div>
    </Router>
  );
}

// 輔助元件：用於保護需要登入才能存取的頁面
const ProtectedRoute = ({ isAuthenticated, children }) => {
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

export default App;
