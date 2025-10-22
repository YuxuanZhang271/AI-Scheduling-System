import React, { useState, useEffect } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell,
  LineChart, Line
} from "recharts";
// Step 1: Import the API function
import { getWeeklyStats } from "../services/api";

const COLORS = ["#1976d2", "#4caf50", "#ff9800", "#9c27b0"];
const DAY_MAP = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]; // For formatting the date

// --- Helper Functions ---
// Converts {work: 40} to [{name: 'work', value: 40}]
const formatPieData = (tasksByType) => {
  if (!tasksByType) return [];
  return Object.entries(tasksByType)
    .filter(([, value]) => value > 0)
    .map(([name, value]) => ({ name, value }));
};

// Converts backend's daily stats into chart-friendly format
const formatBarData = (dailyStats) => {
  if (!dailyStats) return [];
  return dailyStats.map(stat => ({
    day: DAY_MAP[new Date(stat.date + 'T00:00:00').getDay()], // 'T00:00:00' avoids timezone issues
    value: stat.total_tasks
  }));
};

// Gets the start (Monday) and end (Sunday) of a given week
const getWeekRange = (date = new Date()) => {
    const start = new Date(date);
    const day = start.getDay();
    const diff = start.getDate() - day + (day === 0 ? -6 : 1); // Adjust to Monday
    start.setDate(diff);

    const end = new Date(start);
    end.setDate(start.getDate() + 6); // Adjust to Sunday

    return {
        startDate: start.toISOString().split('T')[0],
        endDate: end.toISOString().split('T')[0],
    };
}


export default function WeeklyReport() {
  // Step 2: Create state for all dynamic data
  const [weeklyTasks, setWeeklyTasks] = useState([]);
  const [timeDist, setTimeDist] = useState([]);
  const [avgEnergy, setAvgEnergy] = useState([]);
  const [avgPressure, setAvgPressure] = useState([]);
  const [summaryData, setSummaryData] = useState({});

  const [weekRange, setWeekRange] = useState(getWeekRange());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Step 3: Fetch data when the component loads or the week changes
  useEffect(() => {
    const fetchReport = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await getWeeklyStats(weekRange.startDate, weekRange.endDate);
        // **This is the critical fix:** Get data from 'response.data'
        const data = response.data; 

        // Update all states
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
        console.error("Error fetching weekly report:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [weekRange]); // Re-run when the weekRange (start/end date) changes

  // Handles when the user picks a new date
  const handleDateChange = (e) => {
    const newDate = e.target.valueAsDate || new Date(e.target.value + 'T00:00:00');
    setWeekRange(getWeekRange(newDate));
  };
  
  // Step 4: Handle loading and error states
  if (loading) {
    return <div style={{ padding: "20px", textAlign: "center" }}>Loading Report...</div>;
  }
  if (error) {
    return <div style={{ padding: "20px", textAlign: "center", color: "red" }}>{error}</div>;
  }

  // Step 5: Render charts with data
  return (
    <div style={{ padding: "20px" }}>
      <h2>Weekly Report</h2>
      
      {/* Week Picker */}
      <div style={{ margin: "20px 0" }}>
        <label htmlFor="week-picker" style={{ marginRight: "10px" }}>Pick any day of the week:</label>
        <input
          type="date"
          id="week-picker"
          value={weekRange.startDate} // Show the start of the selected week
          onChange={handleDateChange}
          style={{ padding: "5px", border: "1px solid #ccc", borderRadius: "4px" }}
        />
        <p style={{ color: "#555", fontSize: "0.9em" }}>
          Showing report for: {weekRange.startDate} to {weekRange.endDate}
        </p>
      </div>

      {/* Summary Box */}
      <div style={{ background: "#f9f9f9", padding: "15px", borderRadius: "8px", marginBottom: "20px" }}>
        <h3>Weekly Summary</h3>
        <p>Total Tasks: {summaryData.total}</p>
        <p>Completed Tasks: {summaryData.completed}</p>
        <p>Completion Rate: {summaryData.rate ? (summaryData.rate * 100).toFixed(1) + "%" : "N/A"}</p>
      </div>

      {/* Weekly Tasks Bar Chart */}
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

      {/* Time Distribution Pie Chart */}
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

      {/* Energy & Pressure Line Charts */}
      <div style={{ display: "flex", gap: "20px" }}>
        <ResponsiveContainer width="50%" height={200}>
          <LineChart data={avgEnergy}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line name="Avg Energy" type="monotone" dataKey="value" stroke="#1976d2" />
          </LineChart>
        </ResponsiveContainer>

        <ResponsiveContainer width="50%" height={200}>
          <LineChart data={avgPressure}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line name="Avg Pressure" type="monotone" dataKey="value" stroke="#f44336" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
