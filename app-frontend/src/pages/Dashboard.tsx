// src/pages/Dashboard.tsx
import type { ReactNode } from "react";
import "../main.css";
import { NavBar } from "../components/NavBar";

export const Dashboard = (): ReactNode => {
  return (

    <div className="page-container">
      <NavBar />
      <h1 className="page-title">Dashboard</h1>
      <p className="page-description">
        Welcome to your dashboard. This is where high‑level summaries and quick
        actions will eventually live.
      </p>
    </div>
  );
};