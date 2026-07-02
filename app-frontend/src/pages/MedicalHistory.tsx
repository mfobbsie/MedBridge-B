// src/pages/MedicalHistory.tsx
import { useState } from "react";
import "../main.css";
import "./MedicalHistory.css";

export const MedicalHistory = () => {
  const [activeTab, setActiveTab] = useState<
    "documents" | "charts" | "medications"
  >("documents");

  return (
    <div className="medical-history-page">
      {/* LEFT SIDEBAR */}
      <aside className="sidebar">
        <h1 className="sidebar-title">Profile</h1>

        <div className="sidebar-section">
          <h2>User Information</h2>
          <p>
            Name: John Doe <br />
            Email: john.doe@example.com <br />
            Password: ********
          </p>
        </div>

        <div className="sidebar-section">
          <h2>Personal Contacts</h2>
          <p>
            Mom: Jane Doe <br />
            Dad: Richard Doe <br />
            Sibling: Emily Doe
          </p>
        </div>

        <div className="sidebar-section">
          <h2>Medical Contacts</h2>
          <p>
            Primary Care Physician: Dr. Smith <br />
            Cardiologist: Dr. Johnson <br />
            Dermatologist: Dr. Lee
          </p>
        </div>

        <div className="sidebar-section">
          <h2>Data Sharing</h2>
          <p>
            Allowed to share data with: Dr. Smith, Dr. Johnson <br />
            Allow new contacts: Yes <br />
            MyChart integration: Yes
          </p>
        </div>

        <div className="sidebar-section">
          <h2>General Settings</h2>
          <p>
            Notifications: Yes <br />
            Dark mode: No <br />
            Language: English <br />
            Delete account: No
          </p>
        </div>
      </aside>

      {/* RIGHT MAIN CONTENT */}
      <main className="main-content">
        <h1 className="main-title">Medical History</h1>
        <p className="main-description">
          View your medical documents, charts, and medication history.
        </p>

        {/* Toggle Buttons */}
        <div className="tab-buttons">
          <button
            className={activeTab === "documents" ? "active" : ""}
            onClick={() => setActiveTab("documents")}
          >
            Documents
          </button>

          <button
            className={activeTab === "charts" ? "active" : ""}
            onClick={() => setActiveTab("charts")}
          >
            Charts
          </button>

          <button
            className={activeTab === "medications" ? "active" : ""}
            onClick={() => setActiveTab("medications")}
          >
            Medications
          </button>
        </div>

        {/* Tab Content */}
        <div className="tab-content">
          {activeTab === "documents" && (
            <div>
              <h2>Uploaded Documents</h2>
              <p>No documents uploaded yet.</p>
            </div>
          )}

          {activeTab === "charts" && (
            <div>
              <h2>Medical Charts</h2>
              <p>Your charts will appear here.</p>
            </div>
          )}

          {activeTab === "medications" && (
            <div>
              <h2>Medication History</h2>
              <p>Current and previous medications will appear here.</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};
