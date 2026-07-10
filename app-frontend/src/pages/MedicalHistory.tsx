// src/pages/MedicalHistory.tsx
import { useState } from "react";
import "../main.css";
import "./MedicalHistory.css";

import { useTrustedContactsDomain } from "../hooks/useTrustedContactsDomain";
import { useProviderDomain } from "../hooks/useProviderDomain";
import { useDocumentsDomain } from "../hooks/useDocumentsDomain";
import { useUserSettingsDomain } from "../hooks/useUserSettingsDomain";

export const MedicalHistory = () => {
  const user_id = "demo-user-id"; // Replace with actual user ID logic

  const { data: contacts } = useTrustedContactsDomain();
  const { data: providers } = useProviderDomain();
  const { data: documentList } = useDocumentsDomain();
  const { data: settings } = useUserSettingsDomain(user_id);
  
  
  const [activeTab, setActiveTab] = useState<
    "documents" | "charts" | "medications"
  >("documents");

  

  return (
    <>
      <div className="medical-history-page">
        {/* PROFILE SIDEBAR */}
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
            <h2>Trusted Contacts</h2>
            {contacts?.contactsList?.length ? (
              contacts.contactsList.map((c: any) => (
                <p key={c.id}>
                  {c.label}: {c.name}
                </p>
              ))
            ) : (
              <p>No trusted contacts added yet.</p>
            )}
          </div>

          <div className="sidebar-section">
            <h2>Medical Contacts</h2>
            {providers?.providersList?.length ? (
              providers.providersList.map((p: any) => (
                <p key={p.id}>
                  {p.specialty}: {p.name}
                </p>
              ))
            ) : (
              <p>No providers on file.</p>
            )}
          </div>

          <div className="sidebar-section">
            <h2>Data Sharing</h2>
            <p>
              Trusted Contacts Sharing:{" "}
              {settings?.data?.settings?.allow_trusted_contacts ? "Yes" : "No"}
              <br />
              MyChart Integration:{" "}
              {settings?.data?.settings?.allow_mychart_integration
                ? "Enabled"
                : "Disabled"}
              <br />
              Reminders:{" "}
              {settings?.data?.settings?.enable_reminders ? "On" : "Off"}
            </p>
          </div>

          <div className="sidebar-section">
            <h2>General Settings</h2>
            <p>
              Notifications:{" "}
              {settings?.data?.settings?.enable_reminders ? "Yes" : "No"} <br />
              Language: {profile?.language ?? "English"} <br />
              Delete Account: No
            </p>
          </div>
        </aside>

        {/* MEDICAL HISTORY CONTENT */}
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
                {documents?.documentList?.length ? (
                  documents.documentList.map((doc: any) => (
                    <p key={doc.id}>
                      {doc.label}: {doc.name}
                    </p>
                  ))
                ) : (
                  <p>No documents uploaded yet.</p>
                )}
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
    </>
  );
};
