import React from "react";

export default function CalendarCell({ time, day, task }) {
  return (
    <div className="calendar-cell">
      {task && (
        <div className="task-block">
          <strong>{task.title}</strong>
          <p>{task.time}</p>
        </div>
      )}
    </div>
  );
}
