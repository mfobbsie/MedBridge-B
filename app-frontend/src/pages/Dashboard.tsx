import { useState, type ReactNode } from "react";
import "../main.css";
import "./Dashboard.css";
import CalendarView from "../components/CalendarView";

export const Dashboard = (): ReactNode => {
  const [textValue, setTextValue] = useState<string>("");

  const handleChange = (e:React.ChangeEvent<HTMLTextAreaElement>) => {
  const {value} = e.target;
  setTextValue(() => value)

  }

  return (
    <div className="dashboard-page-container">
      <div>
        <h1 className="dashboard-header-title">Dashboard</h1>
        <p className="dashboard-header-description">
          Welcome to your dashboard. This is where high‑level summaries and
          quick actions will eventually live.
        </p>
      </div>

      <div className="dashboard-calendar-wrapper">
        <CalendarView />
      </div>

      <textarea 
        placeholder="Additional Notes..." 
        className="dashboard-notes"
        value={textValue}
        onChange={handleChange}
         />
    </div>
  );
};
