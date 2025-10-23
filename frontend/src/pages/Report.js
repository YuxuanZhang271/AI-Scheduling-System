import React from "react";
import { Outlet } from "react-router-dom";
export default function Report() {
  return (
    <div className="p-8 h-full">
      <h1 className="text-4xl font-bold text-gray-800 mb-6">Task Reports</h1>
      <div className="bg-white p-6 rounded-lg shadow-md">
        <Outlet />
      </div>
    </div>
  );
}
