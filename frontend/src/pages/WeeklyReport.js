import React from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell,
  LineChart, Line
} from "recharts";

const COLORS = ["#1976d2", "#4caf50", "#ff9800", "#9c27b0"];

export default function WeeklyReport() {
  const weeklyTasks = [
    { day: "Mon", value: 7 },
    { day: "Tue", value: 12 },
    { day: "Wed", value: 16 },
    { day: "Thu", value: 14 },
    { day: "Fri", value: 15 },
    { day: "Sat", value: 10 },
    { day: "Sun", value: 6 },
  ];

  const timeDist = [
    { name: "Work", value: 40 },
    { name: "Fun", value: 25 },
    { name: "Food", value: 10 },
    { name: "Rest", value: 25 },
  ];

  const avgEnergy = [
    { day: "Mon", value: 2 },
    { day: "Tue", value: 3 },
    { day: "Wed", value: 2 },
    { day: "Thu", value: 4 },
    { day: "Fri", value: 5 },
    { day: "Sat", value: 3 },
    { day: "Sun", value: 2 },
  ];

  const avgPressure = [
    { day: "Mon", value: 3 },
    { day: "Tue", value: 2 },
    { day: "Wed", value: 4 },
    { day: "Thu", value: 5 },
    { day: "Fri", value: 4 },
    { day: "Sat", value: 3 },
    { day: "Sun", value: 2 },
  ];

  return (
    <div style={{ padding: "20px" }}>
      <h2>Weekly Report</h2>

      {/* Weekly Tasks 柱状图 */}
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={weeklyTasks}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="day" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="value" fill="#1976d2" />
        </BarChart>
      </ResponsiveContainer>

      {/* Time Distribution 饼图 */}
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie
            data={timeDist}
            cx="50%"
            cy="50%"
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
            label
          >
            {timeDist.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Legend />
        </PieChart>
      </ResponsiveContainer>

      {/* 能量 & 压力 折线图 */}
      <div style={{ display: "flex", gap: "20px" }}>
        <ResponsiveContainer width="50%" height={200}>
          <LineChart data={avgEnergy}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="value" stroke="#1976d2" />
          </LineChart>
        </ResponsiveContainer>

        <ResponsiveContainer width="50%" height={200}>
          <LineChart data={avgPressure}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="value" stroke="#f44336" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
