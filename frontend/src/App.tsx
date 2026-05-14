// src/App.tsx
import React from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import InvestigationLive from "./pages/InvestigationLive";
import History from "./pages/History";
import ReportViewer from "./pages/ReportViewer";
import Config from "./pages/Config";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          {/* Dashboard – new investigation launcher */}
          <Route index element={<Dashboard />} />

          {/* Live investigation feed (navigated to programmatically) */}
          <Route path="live" element={<InvestigationLive />} />

          {/* Investigation history */}
          <Route path="history" element={<History />} />

          {/* Report viewer – with optional job ID */}
          <Route path="report"          element={<ReportViewer />} />
          <Route path="report/:jobId"   element={<ReportViewer />} />

          {/* Configuration */}
          <Route path="config" element={<Config />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
