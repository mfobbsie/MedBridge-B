import type { MedicationResponse } from "../../types/medication";

interface MedicationsTabProps {
  current: MedicationResponse[];
  past: MedicationResponse[];
  onEditMedication: (med: MedicationResponse) => void;
}

export default function MedicationsTab({
  current,
  past,
  onEditMedication,
}: MedicationsTabProps) {
  return (
    <div>
      <h2>Medication History</h2>

      <h3>Current Medications</h3>
      {current.length ? (
        current.map((med) => (
          <div key={med.id} className="list-row">
            <span>
              {med.name} — {med.dosage ?? "Unknown dose"},{" "}
              {med.frequency ?? "Unknown frequency"} (
              {med.is_active ? "Active" : "Inactive"})
            </span>

            <button
              className="edit-button"
              onClick={() => onEditMedication(med)}
            >
              Edit
            </button>
          </div>
        ))
      ) : (
        <p>No current medications.</p>
      )}

      <h3>Past Medications</h3>
      {past.length ? (
        past.map((med) => (
          <div key={med.id} className="list-row">
            <span>
              {med.name} — {med.dosage ?? "Unknown dose"}{" "}
              {med.end_date
                ? `(Ended: ${new Date(med.end_date).toLocaleDateString()})`
                : "(End date unknown)"}
            </span>

            <button
              className="edit-button"
              onClick={() => onEditMedication(med)}
            >
              Edit
            </button>
          </div>
        ))
      ) : (
        <p>No past medications.</p>
      )}
    </div>
  );
}
