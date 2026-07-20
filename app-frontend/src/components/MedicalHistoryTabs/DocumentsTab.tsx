import type { DocumentResponse } from "../../types/documents";
import { API_BASE_URL } from "../../config/env";

interface DocumentsTabProps {
  documents: DocumentResponse[];
  onEditDocument: (doc: DocumentResponse) => void;
  onDeleteDocument: (id: string) => void;
}

export default function DocumentsTab({
  documents,
  onEditDocument,
}: DocumentsTabProps) {
  const sortedDocuments = [...documents].sort(
    (a, b) =>
      new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime(),
  );

  return (
    <div>
      <h2>Uploaded Documents</h2>

      {sortedDocuments.length ? (
        sortedDocuments.map((doc) => (
          <div key={doc.document_id} className="list-row">
            <span>
              <a
                href={`${API_BASE_URL}/documents/${doc.document_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="document-link"
              >
                {doc.file_name}
              </a>
              {" — "}
              {doc.status} ({new Date(doc.uploaded_at).toLocaleDateString()})
            </span>

            <button className="modal-delete" onClick={() => onEditDocument(doc)}>
              delete
            </button>
          </div>
        ))
      ) : (
        <p>No documents uploaded yet.</p>
      )}
    </div>
  );
}

