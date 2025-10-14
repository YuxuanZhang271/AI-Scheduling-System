import React from "react";
import {
  PieChart, Pie, Cell,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from "recharts";

const COLORS = ["#1976d2", "#ff9800", "#4caf50", "#f44336"];

export default function DailyReport() {
  const taskData = [
    { name: "In Schedule", value: 8 },
    { name: "Done", value: 2 },
  ];

  const energyData = [
    { time: "08:00", value: 2 },
    { time: "12:00", value: 3 },
    { time: "16:00", value: 4 },
    { time: "20:00", value: 3 },
  ];

  const pressureData = [
    { time: "08:00", value: 3 },
    { time: "12:00", value: 2 },
    { time: "16:00", value: 4 },
    { time: "20:00", value: 5 },
  ];

  return (
    <div style={{ padding: "20px" }}>
      <h2>Daily Report</h2>

      {/* Tasks 饼图 */}
      <div style={{ display: "flex", gap: "20px" }}>
        <ResponsiveContainer width="50%" height={250}>
          <PieChart>
            <Pie
              data={taskData}
              cx="50%"
              cy="50%"
              labelLine={false}
              outerRadius={100}
              fill="#8884d8"
              dataKey="value"
              label
            >
              {taskData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Legend />
          </PieChart>
        </ResponsiveContainer>

        <div style={{ flex: 1 }}>
          <h3>Task Status</h3>
          {taskData.map((task, i) => (
            <p key={i}>{task.name}: {task.value}</p>
          ))}
        </div>
      </div>

      {/* 能量和压力折线图 */}
      <div style={{ display: "flex", gap: "20px", marginTop: "20px" }}>
        <ResponsiveContainer width="50%" height={200}>
          <LineChart data={energyData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="value" stroke="#1976d2" />
          </LineChart>
        </ResponsiveContainer>

        <ResponsiveContainer width="50%" height={200}>
          <LineChart data={pressureData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="value" stroke="#f44336" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
