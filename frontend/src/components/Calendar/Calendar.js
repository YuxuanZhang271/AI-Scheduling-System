import React, { useEffect, useState } from "react";

// ✅ 修复：将 YYYYMMDDHHMM 格式转换为 Date 对象
function parseTaskTime(timeStr) {
  if (!timeStr || timeStr.length !== 12) {
    console.warn("⚠️ Invalid time format:", timeStr);
    return null;
  }
  try {
    const y = timeStr.slice(0, 4);
    const m = timeStr.slice(4, 6);
    const d = timeStr.slice(6, 8);
    const hh = timeStr.slice(8, 10);
    const mm = timeStr.slice(10, 12);
    const dateStr = `${y}-${m}-${d}T${hh}:${mm}:00`;
    const date = new Date(dateStr);
    
    if (isNaN(date.getTime())) {
      console.warn("⚠️ Invalid date:", dateStr);
      return null;
    }
    
    return date;
  } catch (error) {
    console.warn("⚠️ Error parsing time:", timeStr, error);
    return null;
  }
}

// ✅ 修复：把 Date 转成 datetime-local 需要的本地字符串
function toLocalInputValue(date) {
  const pad = (n) => String(n).padStart(2, "0");
  const y = date.getFullYear();
  const m = pad(date.getMonth() + 1);
  const d = pad(date.getDate());
  const hh = pad(date.getHours());
  const mm = pad(date.getMinutes());
  return `${y}-${m}-${d}T${hh}:${mm}`;
}

export default function Calendar({ tasks = [], onCellClick = () => {}, onTaskClick = () => {} }) {
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

  // ✅ 分类颜色
  const categoryColors = {
    work: "#ffcc80", // 橙
    rest: "#81c784", // 绿
    fun: "#64b5f6",  // 蓝
    food: "#f48fb1", // 粉
  };

  // ✅ 调试：输出任务信息
  useEffect(() => {
    //
    //tasks.forEach((task, index) => {
      //const taskDate = parseTaskTime(task.startTime);
      //console.log(`  Task ${index}:`, {
        //id: task.id,
        //name: task.name,
        //startTime: task.startTime,
        //parsedDate: taskDate?.toString(),
        //duration: task.duration,
        //category: task.category,
        //mode: task.mode
      //});
    //});
    
    // 输出本周日期范围
    //console.log("📅 Week range:", {
      //start: weekStart.toString(),
      //days: days.map((_, i) => {
        //const dayDate = new Date(weekStart);
        //dayDate.setDate(weekStart.getDate() + i);
        //return dayDate.toString();
      //})
    //});
  }, [tasks, weekStart]);

  return (
    <div
      style={{
        maxHeight: "600px",
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
            {days.map((d, dayIndex) => {
              const dayDate = new Date(weekStart);
              dayDate.setDate(weekStart.getDate() + dayIndex);
              return (
                <th
                  key={d}
                  style={{
                    border: "1px solid #ddd",
                    padding: 6,
                    textAlign: "center",
                    background: "#fafafa",
                  }}
                >
                  {d}<br />
                  <span style={{ fontSize: "10px", color: "#666" }}>
                    {dayDate.getDate()}/{dayDate.getMonth() + 1}
                  </span>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {hours.map((h, hourIndex) => (
            <tr key={h} style={{ height: 60 }}>
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

              {days.map((_, dayIndex) => {
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
                      height: "60px",
                      minWidth: "120px",
                    }}
                    onClick={() => onCellClick(cellLocal)}
                  >
                    {/* ✅ 修复：重新编写任务渲染逻辑 */}
                    {tasks.map((task) => {
                      if (!task.startTime) return null;
                      
                      // ✅ 修复：解析任务开始时间
                      const taskStart = parseTaskTime(task.startTime);
                      if (!taskStart) return null;
                      
                      // ✅ 修复：检查任务是否在这一天（基于日期，不是星期几）
                      const taskDayOfMonth = taskStart.getDate();
                      const taskMonth = taskStart.getMonth();
                      const taskYear = taskStart.getFullYear();
                      
                      const cellDayOfMonth = cellDate.getDate();
                      const cellMonth = cellDate.getMonth();
                      const cellYear = cellDate.getFullYear();
                      
                      // ✅ 检查是否是同一天
                      const isSameDay = taskDayOfMonth === cellDayOfMonth && 
                                       taskMonth === cellMonth && 
                                       taskYear === cellYear;
                      
                      if (!isSameDay) return null;
                      
                      // ✅ 检查任务是否在这个小时段内
                      const taskHour = taskStart.getHours();
                      if (taskHour !== hourIndex) return null;
                      
                      // ✅ 计算任务在日历中的位置和高度
                      const taskStartMinutes = taskStart.getHours() * 60 + taskStart.getMinutes();
                      const cellStartMinutes = hourIndex * 60;
                      
                      // ✅ 任务持续时间（小时转换为分钟）
                      const durationMinutes = task.duration * 60;
                      
                      // ✅ 计算任务在单元格内的偏移（像素）
                      const minuteHeight = 60 / 60; // 60px 对应 60分钟
                      const offset = (taskStartMinutes - cellStartMinutes) * minuteHeight;
                      
                      // ✅ 计算任务高度（像素）
                      const height = durationMinutes * minuteHeight;
                      
                      // ✅ 如果任务不在这个单元格可见范围内，不渲染
                      if (offset + height <= 0 || offset >= 60) return null;
                      
                      const color = categoryColors[task.category] || "#e0f7fa";
                      const borderColor = task.mode === "fixed" ? "#d32f2f" : "#1976d2";

                      //console.log(`🎯 Rendering task: ${task.name}`, {
                        //startTime: task.startTime,
                        //parsedDate: taskStart.toString(),
                        //cellDate: cellDate.toString(),
                        //duration: task.duration,
                        //offset,
                        //height,
                        //hourIndex,
                        //dayIndex,
                        //isSameDay
                      //});

                      return (
                        <div
                          key={task.id}
                          style={{
                            position: "absolute",
                            top: offset,
                            left: 2,
                            right: 2,
                            height: Math.max(height, 20), // 最小高度20px
                            background: color,
                            border: `2px solid ${borderColor}`,
                            borderRadius: 4,
                            padding: "2px 4px",
                            fontSize: 11,
                            fontWeight: "bold",
                            overflow: "hidden",
                            cursor: "pointer",
                            zIndex: 2,
                            display: "flex",
                            flexDirection: "column",
                            justifyContent: "center",
                          }}
                          onClick={(e) => {
                            e.stopPropagation();
                            onTaskClick(task);
                          }}
                          title={`${task.name} (${task.mode}) · ${task.category} · ${task.duration}h`}
                        >
                          <div style={{ 
                            display: "flex", 
                            justifyContent: "space-between",
                            alignItems: "center" 
                          }}>
                            <span style={{ 
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              whiteSpace: "nowrap"
                            }}>
                              {task.name}
                            </span>
                            {task.priority && (
                              <span
                                style={{
                                  fontSize: "9px",
                                  background: "rgba(0,0,0,0.2)",
                                  color: "#000",
                                  padding: "1px 3px",
                                  borderRadius: "3px",
                                  marginLeft: "4px",
                                }}
                              >
                                P{task.priority}
                              </span>
                            )}
                          </div>
                          <div style={{ 
                            fontSize: "9px", 
                            color: "#666",
                            marginTop: "1px"
                          }}>
                            {taskStart.getHours().toString().padStart(2, '0')}:
                            {taskStart.getMinutes().toString().padStart(2, '0')} - 
                            {task.duration}h
                          </div>
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
