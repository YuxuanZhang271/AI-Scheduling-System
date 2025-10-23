import React, { useState, useEffect } from "react";
import {
  PieChart, Pie, Cell,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from "recharts";
import { getDailyStats } from "../services/api";

const COLORS = ["#1976d2", "#ff9800", "#4caf50", "#f44336"];

const getTodayString = () => {
  return new Date().toISOString().split('T')[0];
}

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
        console.log(`📊 Fetching daily report for ${selectedDate}`);
        console.log(`👤 User ID: ${userId}`);
        
        // ✅ API 會自動從 localStorage 獲取 user_id
        const response = await getDailyStats(selectedDate);
        const data = response.data;

        console.log('📊 Daily report data:', data);

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
        console.error("❌ Error fetching daily report:", err);
        
        if (err.response && err.response.status === 401) {
          setError("Session expired. Please log in again.");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [selectedDate]);

  if (loading) {
    return (
      <div style={{ padding: "20px", textAlign: "center" }}>
        <div style={{ fontSize: "18px", color: "#666" }}>Loading Report...</div>
      </div>
    );
  }
  
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

      <div style={{ 
        background: "#f9f9f9", 
        padding: "15px", 
        borderRadius: "8px", 
        marginBottom: "20px",
        border: "1px solid #e0e0e0"
      }}>
        <h3 style={{ marginTop: 0 }}>Task Status Summary</h3>
        <div style={{ display: "flex", gap: "30px" }}>
          <p style={{ margin: "5px 0" }}>
            <strong>Total Tasks:</strong> {summaryData.total}
          </p>
          <p style={{ margin: "5px 0" }}>
            <strong>Completed Tasks:</strong> {summaryData.completed}
          </p>
          <p style={{ margin: "5px 0" }}>
            <strong>Completion Rate:</strong> {summaryData.rate}%
          </p>
        </div>
      </div>

      <div style={{ marginBottom: "30px" }}>
        <h3>Task Type Distribution</h3>
        {pieData.length > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ textAlign: "center", padding: "20px", color: "#999" }}>
            No task data available for this date
          </div>
        )}
      </div>

      <div>
        <h3>Energy & Pressure Throughout the Day</h3>
        <div style={{ display: "flex", gap: "20px" }}>
          <ResponsiveContainer width="50%" height={200}>
            <LineChart data={energyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis domain={[0, 5]} />
              <Tooltip />
              <Legend />
              <Line name="Energy" type="monotone" dataKey="value" stroke="#1976d2" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>

          <ResponsiveContainer width="50%" height={200}>
            <LineChart data={pressureData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis domain={[0, 5]} />
              <Tooltip />
              <Legend />
              <Line name="Pressure" type="monotone" dataKey="value" stroke="#f44336" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
