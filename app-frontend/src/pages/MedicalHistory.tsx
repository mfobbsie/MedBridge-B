// src/pages/MedicalHistory.tsx
import type { ReactNode } from "react";

export const MedicalHistory = (): ReactNode => {
  return (
    <div className="page-container">
      <h1 className="page-title">Medical History</h1>
      <p className="page-description">
        Begin building your medical history features here — conditions,
        medications, allergies, surgeries, and more.
      </p>

      {/* Add real components here */}
      <div className="medical-history-content">
        {/* Example placeholder */}
        <p>Medical history details will go here.</p>
      </div>
    </div>
  );
};
