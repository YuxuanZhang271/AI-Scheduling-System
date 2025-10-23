import React, { useState, useEffect } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell,
  LineChart, Line
} from "recharts";
import { getWeeklyStats } from "../services/api";

const COLORS = ["#1976d2", "#4caf50", "#ff9800", "#9c27b0"];
const DAY_MAP = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

// --- Helper Functions ---
/**
 * 將後端的類型統計轉換為餅圖數據
 * {work: 40} -> [{name: 'work', value: 40}]
 */
const formatPieData = (tasksByType) => {
  if (!tasksByType) return [];
  return Object.entries(tasksByType)
    .filter(([, value]) => value > 0)
    .map(([name, value]) => ({ name, value }));
};

/**
 * 將後端的每日統計轉換為柱狀圖數據
 * 包含星期幾的標籤
 */
const formatBarData = (dailyStats) => {
  if (!dailyStats) return [];
  return dailyStats.map(stat => ({
    day: DAY_MAP[new Date(stat.date + 'T00:00:00').getDay()],
    value: stat.total_tasks
  }));
};

/**
 * 獲取給定日期所在週的範圍（週一到週日）
 * @param {Date} date - 任意日期
 * @returns {Object} {startDate, endDate} - 格式為 "YYYY-MM-DD"
 */
const getWeekRange = (date = new Date()) => {
  const start = new Date(date);
  const day = start.getDay();
  const diff = start.getDate() - day + (day === 0 ? -6 : 1); // 調整到週一
  start.setDate(diff);

  const end = new Date(start);
  end.setDate(start.getDate() + 6); // 調整到週日

  return {
    startDate: start.toISOString().split('T')[0],
    endDate: end.toISOString().split('T')[0],
  };
};

export default function WeeklyReport() {
  // 數據狀態
  const [weeklyTasks, setWeeklyTasks] = useState([]);
  const [timeDist, setTimeDist] = useState([]);
  const [avgEnergy, setAvgEnergy] = useState([]);
  const [avgPressure, setAvgPressure] = useState([]);
  const [summaryData, setSummaryData] = useState({});

  // UI 狀態
  const [weekRange, setWeekRange] = useState(getWeekRange());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // ✅ 從 localStorage 獲取 user_id（用於調試）
  const userId = localStorage.getItem("user_id");

  // 當週範圍變化時，重新獲取數據
  useEffect(() => {
    const fetchReport = async () => {
      setLoading(true);
      setError(null);
      
      try {
        console.log(`📊 Fetching weekly report for ${weekRange.startDate} to ${weekRange.endDate}`);
        console.log(`👤 User ID: ${userId}`);
        
        // ✅ API 會自動從 localStorage 獲取 user_id
        const response = await getWeeklyStats(weekRange.startDate, weekRange.endDate);
        const data = response.data;

        console.log("📊 Weekly report data:", data);

        // 更新所有狀態
        setWeeklyTasks(formatBarData(data.daily_stats));
        setTimeDist(formatPieData(data.tasks_by_type));
        setAvgEnergy(data.avg_energy_data || []);
        setAvgPressure(data.avg_pressure_data || []);
        setSummaryData({
          total: data.total_tasks,
          completed: data.completed_tasks,
          rate: data.completion_rate
        });

      } catch (err) {
        setError("Could not load report data. Please try again later.");
        console.error("❌ Error fetching weekly report:", err);
        
        // 如果是認證錯誤，提示用戶重新登入
        if (err.response && err.response.status === 401) {
          setError("Session expired. Please log in again.");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [weekRange]); // 當 weekRange 改變時重新執行

  /**
   * 處理日期選擇器變化
   * 用戶選擇的任意日期會自動計算出該週的範圍
   */
  const handleDateChange = (e) => {
    const newDate = e.target.valueAsDate || new Date(e.target.value + 'T00:00:00');
    setWeekRange(getWeekRange(newDate));
  };
  
  // 載入中狀態
  if (loading) {
    return (
      <div style={{ padding: "20px", textAlign: "center" }}>
        <div style={{ fontSize: "18px", color: "#666" }}>Loading Report...</div>
      </div>
    );
  }
  
  // 錯誤狀態
  if (error) {
    return (
      <div style={{ padding: "20px", textAlign: "center", color: "red" }}>
        <div style={{ fontSize: "18px" }}>{error}</div>
        <button 
          onClick={() => window.location.reload()} 
          style={{ marginTop: "10px", padding: "8px 16px", cursor: "pointer" }}
        >
          Retry
        </button>
      </div>
    );
  }

  // 主要渲染
  return (
    <div style={{ padding: "20px" }}>
      <h2>Weekly Report</h2>
      
      {/* Week Picker */}
      <div style={{ margin: "20px 0" }}>
        <label htmlFor="week-picker" style={{ marginRight: "10px" }}>
          Pick any day of the week:
        </label>
        <input
          type="date"
          id="week-picker"
          value={weekRange.startDate}
          onChange={handleDateChange}
          style={{ 
            padding: "5px", 
            border: "1px solid #ccc", 
            borderRadius: "4px" 
          }}
        />
        <p style={{ color: "#555", fontSize: "0.9em", marginTop: "5px" }}>
          Showing report for: <strong>{weekRange.startDate}</strong> to <strong>{weekRange.endDate}</strong>
        </p>
      </div>

      {/* Summary Box */}
      <div style={{ 
        background: "#f9f9f9", 
        padding: "15px", 
        borderRadius: "8px", 
        marginBottom: "20px",
        border: "1px solid #e0e0e0"
      }}>
        <h3 style={{ marginTop: 0 }}>Weekly Summary</h3>
        <div style={{ display: "flex", gap: "30px" }}>
          <div>
            <p style={{ margin: "5px 0" }}>
              <strong>Total Tasks:</strong> {summaryData.total || 0}
            </p>
            <p style={{ margin: "5px 0" }}>
              <strong>Completed Tasks:</strong> {summaryData.completed || 0}
            </p>
          </div>
          <div>
            <p style={{ margin: "5px 0" }}>
              <strong>Completion Rate:</strong>{" "}
              {summaryData.rate 
                ? (summaryData.rate * 100).toFixed(1) + "%" 
                : "N/A"}
            </p>
          </div>
        </div>
      </div>

      {/* Weekly Tasks Bar Chart */}
      <div style={{ marginBottom: "30px" }}>
        <h3>Daily Task Count</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={weeklyTasks}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar name="Total Tasks" dataKey="value" fill="#1976d2" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Time Distribution Pie Chart */}
      <div style={{ marginBottom: "30px" }}>
        <h3>Task Type Distribution</h3>
        {timeDist.length > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={timeDist}
                cx="50%"
                cy="50%"
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {timeDist.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Legend />
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ textAlign: "center", padding: "20px", color: "#999" }}>
            No task data available for this week
          </div>
        )}
      </div>

      {/* Energy & Pressure Line Charts */}
      <div>
        <h3>Energy & Pressure Trends</h3>
        <div style={{ display: "flex", gap: "20px" }}>
          <ResponsiveContainer width="50%" height={200}>
            <LineChart data={avgEnergy}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis domain={[0, 5]} />
              <Tooltip />
              <Legend />
              <Line 
                name="Avg Energy" 
                type="monotone" 
                dataKey="value" 
                stroke="#1976d2" 
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>

          <ResponsiveContainer width="50%" height={200}>
            <LineChart data={avgPressure}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis domain={[0, 5]} />
              <Tooltip />
              <Legend />
              <Line 
                name="Avg Pressure" 
                type="monotone" 
                dataKey="value" 
                stroke="#f44336" 
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
