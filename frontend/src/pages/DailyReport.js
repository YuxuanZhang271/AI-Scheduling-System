import React, { useState, useEffect } from "react";
import {
  PieChart, Pie, Cell,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from "recharts";
import { getDailyStats } from "../services/api";

const COLORS = ["#1976d2", "#ff9800", "#4caf50", "#f44336"];

const getTodayString = () => new Date().toISOString().split('T')[0];

const formatPieData = (tasksByType) => {
  if (!tasksByType) return [];
  return Object.entries(tasksByType)
    .filter(([, value]) => value > 0)
    .map(([name, value]) => ({ name, value }));
};

export default function DailyReport() {
  const [pieData, setPieData] = useState([]);
  const [energyData, setEnergyData] = useState([]);
  const [pressureData, setPressureData] = useState([]);
  const [summaryData, setSummaryData] = useState({ total: 0, completed: 0, rate: 0 });
  const [selectedDate, setSelectedDate] = useState(getTodayString());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const userId = localStorage.getItem("user_id");

  useEffect(() => {
    const fetchReport = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await getDailyStats(selectedDate);
        const data = response.data;

        setPieData(formatPieData(data.tasks_by_type));
        setEnergyData(data.energy_data || []);
        setPressureData(data.pressure_data || []);
        setSummaryData({ 
          total: data.total_tasks, 
          completed: data.completed_tasks,
          rate: data.completion_rate
        });
      } catch (err) {
        setError("Could not load report data. Please try again later."); 
        if (err.response && err.response.status === 401) {
          setError("Session expired. Please log in again.");
        }
      } finally {
        setLoading(false);
      }
    };
    fetchReport();
  }, [selectedDate]);

  // --- 动态范围计算函数 ---
  const calcDomain = (data) => {
    if (!data || data.length === 0) return [0, 5];
    const values = data.map(p => p.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const diff = max - min || 1; // 避免除零
    const padding = diff * 0.2; // 上下各加 20%
    const yMin = Math.max(0, min - padding);
    const yMax = Math.min(5, max + padding);
    return [yMin, yMax];
  };

  const energyDomain = calcDomain(energyData);
  const pressureDomain = calcDomain(pressureData);

  if (loading) return <div style={{ padding: 20, textAlign: "center" }}>Loading Report...</div>;
  if (error) return (
    <div style={{ padding: 20, textAlign: "center", color: "red" }}>
      <div>{error}</div>
      <button onClick={() => window.location.reload()} style={{ marginTop: 10, padding: "8px 16px" }}>Retry</button>
    </div>
  );

  return (
    <div style={{ padding: "20px" }}>
      <h2>Daily Report - {selectedDate}</h2>

      <div style={{ margin: "20px 0" }}>
        <label htmlFor="report-date" style={{ marginRight: "10px" }}>Select Date:</label>
        <input
          type="date"
          id="report-date"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          style={{ padding: "5px", border: "1px solid #ccc", borderRadius: "4px" }}
        />
      </div>

      {/* --- 任务汇总 --- */}
      <div style={{ background: "#f9f9f9", padding: "15px", borderRadius: "8px", marginBottom: "20px", border: "1px solid #e0e0e0" }}>
        <h3>Task Status Summary</h3>
        <div style={{ display: "flex", gap: "30px" }}>
          <p><strong>Total:</strong> {summaryData.total}</p>
          <p><strong>Completed:</strong> {summaryData.completed}</p>
          <p><strong>Rate:</strong> {summaryData.rate}%</p>
        </div>
      </div>

      {/* --- 饼图 --- */}
      <div style={{ marginBottom: "30px" }}>
        <h3>Task Type Distribution</h3>
        {pieData.length > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                outerRadius={100}
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {pieData.map((entry, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ textAlign: "center", padding: "20px", color: "#999" }}>No task data available</div>
        )}
      </div>

      {/* --- 能量/压力折线 --- */}
      <h3>Energy & Pressure Throughout the Day</h3>
      <div style={{ display: "flex", gap: "20px" }}>
        <ResponsiveContainer width="50%" height={220}>
          <LineChart data={energyData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis domain={energyDomain} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="value" name="Energy" stroke="#1976d2" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>

        <ResponsiveContainer width="50%" height={220}>
          <LineChart data={pressureData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis domain={pressureDomain} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="value" name="Pressure" stroke="#f44336" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
