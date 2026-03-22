import React, { useState, useCallback } from 'react';
import { Upload, File, CheckCircle, AlertCircle, X, FileText, Image as ImageIcon } from 'lucide-react';

interface DocumentUploaderProps {
  applicationId: string;
  documentType: string;
  label: string;
  required?: boolean;
  onUploadComplete?: (documentId: string) => void;
}

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  status: 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
}

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const DocumentUploader: React.FC<DocumentUploaderProps> = ({
  applicationId,
  documentType,
  label,
  required = false,
  onUploadComplete,
}) => {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  const uploadFile = async (file: File) => {
    const fileId = `${Date.now()}-${file.name}`;
    const newFile: UploadedFile = {
      id: fileId,
      name: file.name,
      size: file.size,
      status: 'uploading',
      progress: 0,
    };

    setFiles((prev) => [...prev, newFile]);

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === fileId && f.progress < 90
              ? { ...f, progress: f.progress + 10 }
              : f
          )
        );
      }, 200);

      const response = await fetch(
        `/api/applications/${applicationId}/documents/upload?document_type=${documentType}`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
          body: formData,
        }
      );

      clearInterval(progressInterval);

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const data = await response.json();

      setFiles((prev) =>
        prev.map((f) =>
          f.id === fileId
            ? { ...f, status: 'success', progress: 100 }
            : f
        )
      );

      if (onUploadComplete) {
        onUploadComplete(data.document_id);
      }
    } catch (error) {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === fileId
            ? { ...f, status: 'error', progress: 0, error: 'Upload failed' }
            : f
        )
      );
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    droppedFiles.forEach((file) => {
      if (file.size > 10 * 1024 * 1024) {
        alert(`${file.name} is too large. Maximum size is 10 MB.`);
        return;
      }
      uploadFile(file);
    });
  }, [applicationId, documentType]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    selectedFiles.forEach((file) => {
      if (file.size > 10 * 1024 * 1024) {
        alert(`${file.name} is too large. Maximum size is 10 MB.`);
        return;
      }
      uploadFile(file);
    });
  };

  const removeFile = (fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase();
    if (ext === 'pdf') return <FileText size={20} className="text-red-500" />;
    if (['jpg', 'jpeg', 'png'].includes(ext || '')) return <ImageIcon size={20} className="text-blue-500" />;
    return <File size={20} className="text-gray-500" />;
  };

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-user-text font-body">
        {label}
        {required && <span className="text-risk-very_high ml-1">*</span>}
      </label>

      {/* Drop zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-card p-8 text-center transition-all duration-200
          ${isDragging
            ? 'border-barclays-navy bg-barclays-lightblue'
            : 'border-user-border bg-user-surface hover:border-barclays-blue'
          }
        `}
      >
        <input
          type="file"
          id={`file-${documentType}`}
          onChange={handleFileSelect}
          accept=".pdf,.jpg,.jpeg,.png"
          className="hidden"
          multiple
        />
        <label htmlFor={`file-${documentType}`} className="cursor-pointer">
          <Upload size={32} className="mx-auto mb-3 text-barclays-blue" />
          <p className="text-sm font-medium text-user-text mb-1">
            Drop files here or click to browse
          </p>
          <p className="text-xs text-user-muted">
            PDF, JPG, PNG up to 10 MB
          </p>
        </label>
      </div>

      {/* Uploaded files list */}
      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((file) => (
            <div
              key={file.id}
              className="flex items-center gap-3 p-3 bg-user-surface border border-user-border rounded-card"
            >
              <div className="shrink-0">{getFileIcon(file.name)}</div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-user-text truncate">
                  {file.name}
                </p>
                <p className="text-xs text-user-muted">
                  {formatFileSize(file.size)}
                </p>
                {file.status === 'uploading' && (
                  <div className="mt-1 h-1 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-barclays-teal transition-all duration-300"
                      style={{ width: `${file.progress}%` }}
                    />
                  </div>
                )}
              </div>
              <div className="shrink-0">
                {file.status === 'success' && (
                  <CheckCircle size={20} className="text-risk-low" />
                )}
                {file.status === 'error' && (
                  <AlertCircle size={20} className="text-risk-very_high" />
                )}
                {file.status === 'uploading' && (
                  <div className="w-5 h-5 border-2 border-barclays-teal border-t-transparent rounded-full animate-spin" />
                )}
              </div>
              <button
                onClick={() => removeFile(file.id)}
                className="shrink-0 p-1 hover:bg-gray-100 rounded transition-colors"
              >
                <X size={16} className="text-user-muted" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DocumentUploader;
