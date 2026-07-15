import type { DocumentResponse } from "../../types/documents";

interface DocumentsTabProps {
  documents: DocumentResponse[];
  onEditDocument: (doc: DocumentResponse) => void;
  onDeleteDocument: (id: string) => void;
}

export default function DocumentsTab({
  documents,
  onEditDocument,
  onDeleteDocument,
}: DocumentsTabProps) {
  return (
    <div>
      <h2>Uploaded Documents</h2>

      {documents.length ? (
        documents.map((doc) => (
          <div key={doc.document_id} className="list-row">
            <span>
              {doc.file_name} — {doc.status} (
              {new Date(doc.uploaded_at).toLocaleDateString()})
            </span>

            <button className="edit-button" onClick={() => onEditDocument(doc)}>
              Edit
            </button>

            <button
              className="danger-button"
              onClick={() => onDeleteDocument(doc.document_id)}
            >
              Delete
            </button>
          </div>
        ))
      ) : (
        <p>No documents uploaded yet.</p>
      )}
    </div>
  );
}
