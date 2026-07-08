// src/pages/UploadDocs.tsx
import { useState, type ReactNode } from "react";
import "../main.css";
import "./UploadDocs.css";
import { UploadDocuments } from "../components/UploadDocument";
import { DocumentSummaryPanel } from "../components/DocumentSummaryPanel";
import { useDocumentsDomain } from "../hooks/useDocumentsDomain";

export const UploadDocs = (): ReactNode => {
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const { data, flags, actions, viewConfigs } = useDocumentsDomain(selectedDocumentId || undefined);

  return (
    <div className="grid-container">

      <div className="upload-side-column">
        <UploadDocuments
          selectedDocumentId={selectedDocumentId}
          onSelectDocument={setSelectedDocumentId}
        />
      </div>


      <div className="summary-side-column">
        <DocumentSummaryPanel
          selectedDocumentId={selectedDocumentId}
          activeSummary={data.activeSummary}
          isProcessing={flags.isProcessingFile}
          isEmpty={flags.isSummaryEmpty}
          viewConfigs={viewConfigs}
          onRegenerate={actions.reconstructSummary}
        />
      </div>

    </div>
  );
};