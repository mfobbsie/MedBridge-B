import { useDocumentsDomain } from "../hooks/useDocumentsDomain"
import { ErrorComponent } from "./ErrorComponent";
import { LoadingSpinner } from "./LoadingSpinner";
import { useRef } from "react";



export const UploadDocuments = () => {


    const { data: documents, actions, flags, viewConfigs } = useDocumentsDomain();
    const fileInputRef = useRef<HTMLInputElement>(null);

    if (flags.isPending) return <LoadingSpinner />
    if (flags.hasError) return <ErrorComponent error={flags.errorMessage} />


    const handleContainerClick = () => {
        fileInputRef.current?.click();
    }

   const processFiles = (files: FileList | null) => {
        if (files && files.length > 0) {
            const selectedFile = files[0];
            const formData = new FormData();
            formData.append("file", selectedFile);
            actions.uploadFile(formData);
        }
    }

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        processFiles(event.target.files);
    }

    const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
        event.preventDefault();
    }

    const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
        event.preventDefault();
        processFiles(event.dataTransfer.files);
    }


    return (

        <div className="upload-document-container"
        >

            <div className="upload-header">
                <h2>{viewConfigs.documentLibrary.icon} {viewConfigs.documentLibrary.title}</h2>
                <p>{viewConfigs.documentLibrary.description}</p>
            </div>



            <div className="upload-background-container"
                onClick={handleContainerClick}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                style={{ 
                    cursor: "pointer",
                    border: "2px dashed #3182ce",    
                    backgroundColor: "#f7fafc",       
                    padding: "40px 20px",             
                    borderRadius: "8px",              
                    textAlign: "center"               
                }}
            >
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    style={{ display: "none" }}
                />
                <p>{flags.isProcessingFile
                    ? "⏳ Uploading..."
                    : `+ ${viewConfigs.documentLibrary.title || "Upload Document"}`}
                </p>
                <p>Click or Drop Here</p>
            </div>


            {flags.isDocumentListEmpty ? (
                <div className="empty-documents-list">
                    <span className="empty-icon">{viewConfigs.emptyLibrary.icon}</span>
                    <h4>{viewConfigs.emptyLibrary.title}</h4>
                    <p>{viewConfigs.emptyLibrary.description}</p>
                </div>
            ) : (
                <div className="documents-grid">
                    {documents.documentList?.map((doc) => (
                        <div key={doc.document_id} className="document-card">
                            <div className="document-info">
                                <h4>{doc.file_name}</h4>
                                <p>{doc.uploaded_at}</p>
                            </div>
                            <button
                                className="delete-document-btn"
                                onClick={() => actions.deleteFile(doc.document_id)}
                                disabled={flags.isDeletingFile === doc.document_id}>
                                {flags.isDeletingFile === doc.document_id ? "Removing..." : "🗑️"}
                            </button>
                        </div>
                    ))}
                </div>
            )
            }
        </div >
    )
}