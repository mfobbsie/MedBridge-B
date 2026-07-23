import type { MedicationResponse } from "../../types/medication";

interface MedicationsTabProps {
  current: MedicationResponse[];
  past: MedicationResponse[];
  onEditMedication: (med: MedicationResponse | null) => void;
  onAddMedication: () => void;
  onStopMedication: (med: MedicationResponse) => void;
  onStartMedication: (med: MedicationResponse) => void;
  onDeleteMedication: (id: string) => void;
}

export default function MedicationsTab({
  current,
  past,
  onEditMedication,
  onAddMedication,
  onStopMedication,
  onStartMedication,
  onDeleteMedication,
}: MedicationsTabProps) {
  return (
    <div>
      {/* MAIN HEADER WITH ADD BUTTON */}
      <div className="section-header">
        <h2>Medication History</h2>

        <button className="add-meds-button" onClick={onAddMedication}>
          <span className="pill-icon">💊</span> Add Medication
        </button>
      </div>

      {/* CURRENT MEDICATIONS */}
      <div className="section-header">
        <h3>Current Medications</h3>
      </div>

      {current.length ? (
        current.map((med) => (
          <div key={med.id} className="list-row">
            <span>
              {med.name} — {med.dosage ?? "Unknown dose"},{" "}
              {med.frequency ?? "Unknown frequency"}
            </span>

            <div className="med-actions">
              <button onClick={() => onStopMedication(med)}>Stop</button>
              <button onClick={() => onEditMedication(med)}>Edit</button>
              <button
                className="modal-delete"
                onClick={() => onDeleteMedication(med.id)}
              >
                Delete
              </button>
            </div>
          </div>
        ))
      ) : (
        <p>No current medications.</p>
      )}

      {/* PAST MEDICATIONS */}
      <div className="section-header">
        <h3>Past Medications</h3>
      </div>

      {past.length ? (
        past.map((med) => (
          <div key={med.id} className="list-row">
            <span>
              {med.name} — {med.dosage ?? "Unknown dose"}{" "}
              {med.end_date
                ? `(Ended: ${new Date(med.end_date).toLocaleDateString()})`
                : "(End date unknown)"}
            </span>

            <div className="med-actions">
              <button onClick={() => onStartMedication(med)}>Start</button>
              <button onClick={() => onEditMedication(med)}>Edit</button>
              <button
                className="modal-delete"
                onClick={() => onDeleteMedication(med.id)}
              >
                Delete
              </button>
            </div>
          </div>
        ))
      ) : (
        <p>No past medications.</p>
      )}
    </div>
  );
}
