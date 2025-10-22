import React, { useState, useEffect } from "react";
import {
  PieChart, Pie, Cell,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from "recharts";
// Step 1: Import the API function
import { getDailyStats } from "../services/api";

const COLORS = ["#1976d2", "#ff9800", "#4caf50", "#f44336"];

// --- Helper Functions ---
// Gets today's date in "YYYY-MM-DD" format
const getTodayString = () => {
  return new Date().toISOString().split('T')[0];
}

// Converts backend data {work: 2} to chart data [{name: 'work', value: 2}]
const formatPieData = (tasksByType) => {
  if (!tasksByType) return [];
  return Object.entries(tasksByType)
    .filter(([, value]) => value > 0) // Only show categories that have tasks
    .map(([name, value]) => ({ name, value }));
};


export default function DailyReport() {
  // Step 2: Create state to hold data from the API
  const [pieData, setPieData] = useState([]);
  const [energyData, setEnergyData] = useState([]);
  const [pressureData, setPressureData] = useState([]);
  const [summaryData, setSummaryData] = useState({ total: 0, completed: 0 });
  
  const [selectedDate, setSelectedDate] = useState(getTodayString());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Step 3: Fetch data when the component loads or the date changes
  useEffect(() => {
    const fetchReport = async () => {
      setLoading(true);
      setError(null);
      try {
        // Call the API
        const response = await getDailyStats(selectedDate);
        
        // **This is the critical fix:** We must get the data from 'response.data'
        const data = response.data; 

        // Update all our states with the data from the API
        setPieData(formatPieData(data.tasks_by_type));
        setEnergyData(data.energy_data || []);
        setPressureData(data.pressure_data || []);
        setSummaryData({ 
          total: data.total_tasks, 
          completed: data.completed_tasks 
        });
        
      } catch (err) {
        // If the API call fails, set the error message
        setError("Could not load report data. Please try again later."); 
        console.error("Error fetching daily report:", err);
      } finally {
        // Stop loading
        setLoading(false);
      }
    };

    fetchReport();
  }, [selectedDate]); // This code re-runs when the user picks a new date

  // Step 4: Show loading or error messages
  if (loading) {
    return <div style={{ padding: "20px", textAlign: "center" }}>Loading Report...</div>;
  }
  if (error) {
    return <div style={{ padding: "20px", textAlign: "center", color: "red" }}>{error}</div>;
  }

  // Step 5: Render the report with the data
  return (
    <div style={{ padding: "20px" }}>
      <h2>Daily Report</h2>

      {/* Date Picker */}
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

      {/* Task Pie Chart & Summary */}
      <div style={{ display: "flex", gap: "20px", alignItems: "center" }}>
        <ResponsiveContainer width="50%" height={250}>
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              labelLine={false}
              outerRadius={100}
              fill="#8884d8"
              dataKey="value"
              // Add percentage label to the chart
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

        <div style={{ flex: 1 }}>
          <h3>Task Status Summary</h3>
          {/* This part now shows the summary data */}
          <p>Total Tasks: {summaryData.total}</p>
          <p>Completed Tasks: {summaryData.completed}</p>
          <p>Completion Rate: {summaryData.total > 0 
            ? ((summaryData.completed / summaryData.total) * 100).toFixed(1) + "%" 
            : "N/A"}
          </p>
        </div>
      </div>

      {/* Energy & Pressure Line Charts */}
      <div style={{ display: "flex", gap: "20px", marginTop: "20px" }}>
        <ResponsiveContainer width="50%" height={200}>
          <LineChart data={energyData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line name="Energy" type="monotone" dataKey="value" stroke="#1976d2" />
          </LineChart>
        </ResponsiveContainer>

        <ResponsiveContainer width="50%" height={200}>
          <LineChart data={pressureData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line name="Pressure" type="monotone" dataKey="value" stroke="#f44336" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
