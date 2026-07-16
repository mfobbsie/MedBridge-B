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
              <a
                href={`http://localhost:8000/documents/${doc.document_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="document-link"
              >
                {doc.file_name}
              </a>
              {" — "}
              {doc.status} ({new Date(doc.uploaded_at).toLocaleDateString()})
            </span>

            <button className="edit-button" onClick={() => onEditDocument(doc)}>
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
