import React, { useEffect, useState } from "react";

// 把 Date 转成 datetime-local 需要的本地字符串
function toLocalInputValue(date) {
  const pad = (n) => String(n).padStart(2, "0");
  const y = date.getFullYear();
  const m = pad(date.getMonth() + 1);
  const d = pad(date.getDate());
  const hh = pad(date.getHours());
  const mm = pad(date.getMinutes());
  return `${y}-${m}-${d}T${hh}:${mm}`;
}

export default function Calendar({ tasks, onCellClick, onTaskClick }) {
  const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const hours = Array.from({ length: 24 }, (_, i) =>
    `${i.toString().padStart(2, "0")}:00`
  );

  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 60 * 1000);
    return () => clearInterval(timer);
  }, []);

  // 本周的周日作为起点
  const weekStart = new Date(currentTime);
  weekStart.setHours(0, 0, 0, 0);
  weekStart.setDate(currentTime.getDate() - currentTime.getDay());

  // 分类颜色
  const categoryColors = {
    work: "#ffcc80", // 橙
    rest: "#81c784", // 绿
    fun: "#64b5f6",  // 蓝
    food: "#f48fb1", // 粉
  };

  return (
    <div
      style={{
        maxHeight: "600px", // 可调节
        overflowY: "auto",
        border: "1px solid #ccc",
        borderRadius: "8px",
        background: "#fff",
      }}
    >
      <table style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            <th style={{ width: 60 }}></th>
            {days.map((d) => (
              <th
                key={d}
                style={{
                  border: "1px solid #ddd",
                  padding: 6,
                  textAlign: "center",
                  background: "#fafafa",
                }}
              >
                {d}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {hours.map((h, hourIndex) => (
            <tr key={h} style={{ height: 30 }}>
              {/* 时间刻度 */}
              <td
                style={{
                  border: "1px solid #ddd",
                  padding: 6,
                  textAlign: "right",
                  fontSize: 12,
                  background: "#f8f8f8",
                }}
              >
                {h}
              </td>

              {/* 每天格子 */}
              {days.map((_, dayIndex) => {
                // 当前格子时间
                const cellDate = new Date(weekStart);
                cellDate.setDate(weekStart.getDate() + dayIndex);
                cellDate.setHours(hourIndex, 0, 0, 0);
                const cellLocal = toLocalInputValue(cellDate);

                return (
                  <td
                    key={`${dayIndex}-${hourIndex}`}
                    style={{
                      border: "1px solid #ddd",
                      position: "relative",
                      verticalAlign: "top",
                      cursor: "pointer",
                      height: "30px",
                    }}
                    onClick={() => onCellClick(cellLocal)}
                  >
                    {/* 渲染任务 */}
                    {tasks.map((task) => {
                      if (!task.startTime) return null;
                      const start = new Date(task.startTime);
                      const tDay = start.getDay();
                      if (tDay !== dayIndex) return null;

                      const tHour = start.getHours();
                      const tMinute = start.getMinutes();
                      const duration = parseInt(task.duration) || 1;
                      const height = 30 * duration;
                      const offset = (tHour - hourIndex) * 30 + (tMinute / 60) * 30;

                      // 如果任务不在这一行对应的时间范围，就不显示
                      if (offset < 0 || offset >= 30) return null;

                      const color = categoryColors[task.category] || "#e0f7fa";

                      return (
                        <div
                          key={task.id}
                          style={{
                            position: "absolute",
                            top: offset,
                            left: 0,
                            right: 0,
                            height,
                            background: color,
                            border: "2px solid #00838f",
                            borderRadius: 6,
                            padding: "4px",
                            fontSize: 12,
                            fontWeight: "bold",
                            overflow: "hidden",
                            cursor: "pointer",
                            zIndex: 2,
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                          }}
                          onClick={(e) => {
                            e.stopPropagation();
                            onTaskClick(task);
                          }}
                          title={`${task.name} · ${task.category} · P${task.priority}`}
                        >
                          <span>{task.name}</span>
                          {task.priority && (
                            <span
                              style={{
                                fontSize: "10px",
                                background: "rgba(0,0,0,0.2)",
                                color: "#000",
                                padding: "2px 4px",
                                borderRadius: "4px",
                              }}
                            >
                              P{task.priority}
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
