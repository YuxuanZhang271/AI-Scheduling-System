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

  return (
    // ✅ 关键修改：移除 maxHeight，改为占满父容器
    <div
      style={{
        height: "100%", // ✅ 改为 100%，占满父容器
        display: "flex",
        flexDirection: "column",
        border: "1px solid #ccc",
        borderRadius: "8px",
        background: "#fff",
        overflow: "hidden", // ✅ 外层不滚动
      }}
    >
      {/* ✅ 新增：表格容器，允许内部滚动 */}
      <div style={{
        flex: 1,
        overflowY: "auto",
        overflowX: "auto",
      }}>
        <table style={{ 
          borderCollapse: "collapse", 
          width: "100%",
          minWidth: "900px" // ✅ 设置最小宽度，防止过度压缩
        }}>
          <thead>
            <tr>
              <th style={{ 
                width: 60,
                position: "sticky", // ✅ 粘性定位
                top: 0,
                zIndex: 10,
                background: "#fafafa"
              }}></th>
              {days.map((d, dayIndex) => {
                const dayDate = new Date(weekStart);
                dayDate.setDate(weekStart.getDate() + dayIndex);
                
                // ✅ 检查是否是今天
                const isToday = dayDate.toDateString() === currentTime.toDateString();
                
                return (
                  <th
                    key={d}
                    style={{
                      border: "1px solid #ddd",
                      padding: 6,
                      textAlign: "center",
                      background: isToday ? "#e3f2fd" : "#fafafa", // ✅ 今天高亮
                      position: "sticky", // ✅ 粘性定位
                      top: 0,
                      zIndex: 10,
                      fontWeight: isToday ? "bold" : "normal",
                    }}
                  >
                    {d}<br />
                    <span style={{ 
                      fontSize: "10px", 
                      color: isToday ? "#1976d2" : "#666" // ✅ 今天用蓝色
                    }}>
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
                    position: "sticky", // ✅ 粘性定位
                    left: 0,
                    zIndex: 5,
                  }}
                >
                  {h}
                </td>

                {days.map((_, dayIndex) => {
                  const cellDate = new Date(weekStart);
                  cellDate.setDate(weekStart.getDate() + dayIndex);
                  cellDate.setHours(hourIndex, 0, 0, 0);
                  const cellLocal = toLocalInputValue(cellDate);

                  // ✅ 检查是否是当前时间的单元格
                  const isCurrentHour = 
                    cellDate.toDateString() === currentTime.toDateString() &&
                    hourIndex === currentTime.getHours();

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
                        background: isCurrentHour ? "#fff9e6" : "transparent", // ✅ 当前时间高亮
                      }}
                      onClick={() => onCellClick(cellLocal)}
                    >
                      {/* ✅ 如果是当前时间，显示时间线 */}
                      {isCurrentHour && (
                        <div
                          style={{
                            position: "absolute",
                            top: (currentTime.getMinutes() / 60) * 60,
                            left: 0,
                            right: 0,
                            height: "2px",
                            background: "#f44336",
                            zIndex: 10,
                          }}
                        >
                          <div
                            style={{
                              position: "absolute",
                              left: "-4px",
                              top: "-4px",
                              width: "10px",
                              height: "10px",
                              borderRadius: "50%",
                              background: "#f44336",
                            }}
                          />
                        </div>
                      )}

                      {/* 任务渲染 */}
                      {tasks.map((task) => {
                        if (!task.startTime) return null;
                        
                        const taskStart = parseTaskTime(task.startTime);
                        if (!taskStart) return null;
                        
                        // 检查任务是否在这一天
                        const taskDayOfMonth = taskStart.getDate();
                        const taskMonth = taskStart.getMonth();
                        const taskYear = taskStart.getFullYear();
                        
                        const cellDayOfMonth = cellDate.getDate();
                        const cellMonth = cellDate.getMonth();
                        const cellYear = cellDate.getFullYear();
                        
                        const isSameDay = taskDayOfMonth === cellDayOfMonth && 
                                         taskMonth === cellMonth && 
                                         taskYear === cellYear;
                        
                        if (!isSameDay) return null;
                        
                        // 检查任务是否在这个小时段内
                        const taskHour = taskStart.getHours();
                        if (taskHour !== hourIndex) return null;
                        
                        // 计算任务在日历中的位置和高度
                        const taskStartMinutes = taskStart.getHours() * 60 + taskStart.getMinutes();
                        const cellStartMinutes = hourIndex * 60;
                        
                        const durationMinutes = task.duration * 60;
                        const minuteHeight = 60 / 60;
                        const offset = (taskStartMinutes - cellStartMinutes) * minuteHeight;
                        const height = durationMinutes * minuteHeight;
                        
                        if (offset + height <= 0 || offset >= 60) return null;
                        
                        const color = categoryColors[task.category] || "#e0f7fa";
                        const borderColor = task.mode === "fixed" ? "#d32f2f" : "#1976d2";

                        return (
                          <div
                            key={task.id}
                            style={{
                              position: "absolute",
                              top: offset,
                              left: 2,
                              right: 2,
                              height: Math.max(height, 20),
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
                              boxShadow: "0 1px 3px rgba(0,0,0,0.2)", // ✅ 添加阴影
                              transition: "all 0.2s ease", // ✅ 添加过渡动画
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.transform = "scale(1.02)";
                              e.currentTarget.style.zIndex = "20";
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.transform = "scale(1)";
                              e.currentTarget.style.zIndex = "2";
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
                                    flexShrink: 0,
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

      {/* ✅ 新增：图例说明 */}
      <div style={{
        padding: "10px 15px",
        borderTop: "1px solid #ddd",
        background: "#fafafa",
        display: "flex",
        gap: "15px",
        fontSize: "12px",
        flexWrap: "wrap",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
          <div style={{ 
            width: "12px", 
            height: "12px", 
            border: "2px solid #d32f2f",
            borderRadius: "2px",
            background: "#ffcc80"
          }} />
          <span>Fixed Task</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
          <div style={{ 
            width: "12px", 
            height: "12px", 
            border: "2px solid #1976d2",
            borderRadius: "2px",
            background: "#ffcc80"
          }} />
          <span>Flexible Task</span>
        </div>
        {Object.entries(categoryColors).map(([category, color]) => (
          <div key={category} style={{ display: "flex", alignItems: "center", gap: "5px" }}>
            <div style={{ 
              width: "12px", 
              height: "12px", 
              background: color,
              borderRadius: "2px",
              border: "1px solid #ccc"
            }} />
            <span style={{ textTransform: "capitalize" }}>{category}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
