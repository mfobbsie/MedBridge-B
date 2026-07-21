import type { DocumentResponse } from "../../types/documents";
import {useGetDocumentFileUrl} from "../../api/documents.queries";

interface DocumentsTabProps {
  documents: DocumentResponse[];
  onEditDocument: (doc: DocumentResponse) => void;
  onDeleteDocument: (id: string) => void;
}

export default function DocumentsTab({
  documents,
  onEditDocument,
}: DocumentsTabProps) {
  const { mutate: getFileUrl } = useGetDocumentFileUrl();

  const handleOpenDocument = (document_id: string) => {
    getFileUrl(document_id, {
      onSuccess: (data) => {
        window.open(data.url, "_blank", "noopener,noreferrer");
      },
    });
  };

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
              <span
                onClick={() => handleOpenDocument(doc.document_id)}
                className="document-link"
                style={{ cursor: "pointer" }}
              >
                {doc.file_name}
              </span>
              {" — "}
              {doc.status} ({new Date(doc.uploaded_at).toLocaleDateString()})
            </span>

            <button
              className="modal-delete"
              onClick={() => onEditDocument(doc)}
            >
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

