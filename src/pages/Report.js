// src/pages/Report.js
import React from "react";
import { Outlet } from "react-router-dom";

export default function Report() {
  return (
    <div style={{ flex: 1, background: "#fafafa", padding: "20px" }}>
      <Outlet />
    </div>
  );
}
