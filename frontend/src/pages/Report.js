import React from "react";
// Import Outlet and NavLink for nested routing
import { Outlet, NavLink } from "react-router-dom";

// Helper function to determine the style for active links
const getLinkClass = ({ isActive }) => {
  const baseClasses = "px-4 py-2 text-lg font-semibold transition-colors duration-200";
  // Apply different styles if the link is active
  if (isActive) {
    return `${baseClasses} text-blue-600 border-b-2 border-blue-600`;
  }
  return `${baseClasses} text-gray-500 hover:text-gray-800`;
};

export default function Report() {
  return (
    <div className="p-8 h-full">
      <h1 className="text-4xl font-bold text-gray-800 mb-6">Task Reports</h1>
      
      {/* Navigation tabs to switch between Daily and Weekly */}
      <nav className="flex items-center border-b border-gray-200 mb-6">
        {/* The "to" path is relative. 
          "daily" becomes "/report/daily" 
          "weekly" becomes "/report/weekly"
        */}
        <NavLink to="daily" className={getLinkClass}>
          Daily Report
        </NavLink>
        <NavLink to="weekly" className={getLinkClass}>
          Weekly Report
        </NavLink>
      </nav>

      {/* The <Outlet /> is the container where 
        <DailyReport /> or <WeeklyReport /> will be rendered.
      */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <Outlet />
      </div>
    </div>
  );
}
