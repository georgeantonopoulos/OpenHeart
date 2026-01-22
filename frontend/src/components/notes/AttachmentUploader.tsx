'use client';

/**
 * AttachmentUploader Component
 *
 * Drag-and-drop file upload for clinical note attachments with:
 * - Multiple file support
 * - File type validation
 * - Upload progress indicators
 * - Preview thumbnails
 * - OCR status display
 */

import React, { useState, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Upload,
  File,
  FileText,
  Image,
  X,
  Check,
  Loader2,
  AlertCircle,
  Eye,
  Download,
  Trash2,
} from 'lucide-react';

type FileType = 'pdf' | 'docx' | 'doc' | 'image' | 'txt' | 'unknown';
type UploadStatus = 'pending' | 'uploading' | 'processing' | 'completed' | 'failed';
type ExtractionStatus = 'pending' | 'processing' | 'completed' | 'failed';

interface AttachmentFile {
  id: string;
  file: File;
  fileType: FileType;
  uploadStatus: UploadStatus;
  uploadProgress: number;
  extractionStatus?: ExtractionStatus;
  error?: string;
  previewUrl?: string;
  attachmentId?: number;
}

interface ExistingAttachment {
  attachmentId: number;
  fileName: string;
  originalFileName: string;
  fileType: string;
  mimeType: string;
  fileSizeBytes: number;
  extractionStatus: string;
  pageCount?: number;
  imageWidth?: number;
  imageHeight?: number;
}

interface AttachmentUploaderProps {
  noteId: number;
  existingAttachments?: ExistingAttachment[];
  onUpload: (file: File) => Promise<{ attachmentId: number; extractionStatus: string }>;
  onDelete?: (attachmentId: number) => Promise<void>;
  onPreview?: (attachmentId: number) => void;
  onDownload?: (attachmentId: number) => void;
  maxFileSize?: number; // in bytes
  className?: string;
}

const ACCEPTED_TYPES: Record<string, FileType> = {
  'application/pdf': 'pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
  'application/msword': 'doc',
  'image/jpeg': 'image',
  'image/png': 'image',
  'image/tiff': 'image',
  'image/bmp': 'image',
  'image/webp': 'image',
  'text/plain': 'txt',
};

const FILE_TYPE_ICONS: Record<FileType, typeof File> = {
  pdf: FileText,
  docx: FileText,
  doc: FileText,
  image: Image,
  txt: File,
  unknown: File,
};

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileType(file: File): FileType {
  return ACCEPTED_TYPES[file.type] || 'unknown';
}

function generateId(): string {
  return Math.random().toString(36).substring(2, 9);
}

export function AttachmentUploader({
  noteId,
  existingAttachments = [],
  onUpload,
  onDelete,
  onPreview,
  onDownload,
  maxFileSize = 50 * 1024 * 1024, // 50MB default
  className = '',
}: AttachmentUploaderProps) {
  const { t } = useTranslation('cardiology');
  const [files, setFiles] = useState<AttachmentFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback(
    (file: File): string | null => {
      if (file.size > maxFileSize) {
        return `File too large. Maximum size: ${formatFileSize(maxFileSize)}`;
      }
      if (!ACCEPTED_TYPES[file.type]) {
        return 'Unsupported file type. Accepted: PDF, DOCX, JPG, PNG, TXT';
      }
      return null;
    },
    [maxFileSize]
  );

  const uploadFile = useCallback(
    async (attachmentFile: AttachmentFile) => {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === attachmentFile.id
            ? { ...f, uploadStatus: 'uploading' as UploadStatus, uploadProgress: 0 }
            : f
        )
      );

      try {
        // Simulate progress (actual progress would come from fetch with upload listener)
        const progressInterval = setInterval(() => {
          setFiles((prev) =>
            prev.map((f) =>
              f.id === attachmentFile.id && f.uploadProgress < 90
                ? { ...f, uploadProgress: f.uploadProgress + 10 }
                : f
            )
          );
        }, 200);

        const result = await onUpload(attachmentFile.file);

        clearInterval(progressInterval);

        setFiles((prev) =>
          prev.map((f) =>
            f.id === attachmentFile.id
              ? {
                  ...f,
                  uploadStatus: 'completed' as UploadStatus,
                  uploadProgress: 100,
                  attachmentId: result.attachmentId,
                  extractionStatus: result.extractionStatus as ExtractionStatus,
                }
              : f
          )
        );
      } catch (error) {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === attachmentFile.id
              ? {
                  ...f,
                  uploadStatus: 'failed' as UploadStatus,
                  error: error instanceof Error ? error.message : 'Upload failed',
                }
              : f
          )
        );
      }
    },
    [onUpload]
  );

  const handleFiles = useCallback(
    (newFiles: FileList | null) => {
      if (!newFiles) return;

      const filesToAdd: AttachmentFile[] = [];

      Array.from(newFiles).forEach((file) => {
        const error = validateFile(file);
        const fileType = getFileType(file);

        // Create preview URL for images
        let previewUrl: string | undefined;
        if (fileType === 'image') {
          previewUrl = URL.createObjectURL(file);
        }

        const attachmentFile: AttachmentFile = {
          id: generateId(),
          file,
          fileType,
          uploadStatus: error ? 'failed' : 'pending',
          uploadProgress: 0,
          error: error || undefined,
          previewUrl,
        };

        filesToAdd.push(attachmentFile);

        // Auto-start upload if valid
        if (!error) {
          setTimeout(() => uploadFile(attachmentFile), 100);
        }
      });

      setFiles((prev) => [...prev, ...filesToAdd]);
    },
    [validateFile, uploadFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      handleFiles(e.target.files);
      // Reset input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    },
    [handleFiles]
  );

  const removeFile = useCallback((id: string) => {
    setFiles((prev) => {
      const file = prev.find((f) => f.id === id);
      if (file?.previewUrl) {
        URL.revokeObjectURL(file.previewUrl);
      }
      return prev.filter((f) => f.id !== id);
    });
  }, []);

  const handleDeleteExisting = useCallback(
    async (attachmentId: number) => {
      if (!onDelete) return;
      try {
        await onDelete(attachmentId);
      } catch (error) {
        console.error('Failed to delete attachment:', error);
      }
    },
    [onDelete]
  );

  const FileStatusBadge = ({ status }: { status: UploadStatus | ExtractionStatus }) => {
    switch (status) {
      case 'pending':
        return (
          <span className="text-xs text-gray-500 flex items-center">
            <Loader2 className="h-3 w-3 mr-1 animate-spin" />
            Pending
          </span>
        );
      case 'uploading':
        return (
          <span className="text-xs text-blue-600 flex items-center">
            <Loader2 className="h-3 w-3 mr-1 animate-spin" />
            Uploading
          </span>
        );
      case 'processing':
        return (
          <span className="text-xs text-amber-600 flex items-center">
            <Loader2 className="h-3 w-3 mr-1 animate-spin" />
            OCR Processing
          </span>
        );
      case 'completed':
        return (
          <span className="text-xs text-green-600 flex items-center">
            <Check className="h-3 w-3 mr-1" />
            Complete
          </span>
        );
      case 'failed':
        return (
          <span className="text-xs text-red-600 flex items-center">
            <AlertCircle className="h-3 w-3 mr-1" />
            Failed
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragging
            ? 'border-blue-400 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={Object.keys(ACCEPTED_TYPES).join(',')}
          onChange={handleInputChange}
          className="hidden"
        />
        <Upload
          className={`h-10 w-10 mx-auto mb-3 ${
            isDragging ? 'text-blue-500' : 'text-gray-400'
          }`}
        />
        <p className="text-gray-600 mb-1">
          <span className="font-medium text-blue-600">Click to upload</span> or
          drag and drop
        </p>
        <p className="text-sm text-gray-500">
          PDF, DOCX, JPG, PNG, TXT (max {formatFileSize(maxFileSize)})
        </p>
      </div>

      {/* Upload Queue */}
      {files.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Uploads</h4>
          {files.map((file) => {
            const FileIcon = FILE_TYPE_ICONS[file.fileType];

            return (
              <div
                key={file.id}
                className={`flex items-center p-3 border rounded-lg ${
                  file.uploadStatus === 'failed'
                    ? 'border-red-200 bg-red-50'
                    : 'border-gray-200 bg-white'
                }`}
              >
                {/* Preview/Icon */}
                <div className="flex-shrink-0 mr-3">
                  {file.previewUrl ? (
                    <img
                      src={file.previewUrl}
                      alt=""
                      className="h-10 w-10 object-cover rounded"
                    />
                  ) : (
                    <FileIcon className="h-10 w-10 text-gray-400" />
                  )}
                </div>

                {/* File Info */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {file.file.name}
                  </p>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-500">
                      {formatFileSize(file.file.size)}
                    </span>
                    <FileStatusBadge
                      status={file.extractionStatus || file.uploadStatus}
                    />
                  </div>
                  {file.error && (
                    <p className="text-xs text-red-600 mt-1">{file.error}</p>
                  )}
                </div>

                {/* Progress Bar */}
                {file.uploadStatus === 'uploading' && (
                  <div className="w-24 mx-3">
                    <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 transition-all"
                        style={{ width: `${file.uploadProgress}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Remove Button */}
                <button
                  onClick={() => removeFile(file.id)}
                  className="p-1 hover:bg-gray-100 rounded"
                >
                  <X className="h-4 w-4 text-gray-400" />
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Existing Attachments */}
      {existingAttachments.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Attachments</h4>
          {existingAttachments.map((attachment) => {
            const fileType = (attachment.fileType as FileType) || 'unknown';
            const FileIcon = FILE_TYPE_ICONS[fileType];

            return (
              <div
                key={attachment.attachmentId}
                className="flex items-center p-3 border rounded-lg bg-white"
              >
                <FileIcon className="h-8 w-8 text-gray-400 mr-3" />

                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {attachment.originalFileName}
                  </p>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-500">
                      {formatFileSize(attachment.fileSizeBytes)}
                    </span>
                    {attachment.pageCount && (
                      <span className="text-xs text-gray-500">
                        {attachment.pageCount} pages
                      </span>
                    )}
                    <FileStatusBadge
                      status={attachment.extractionStatus as ExtractionStatus}
                    />
                  </div>
                </div>

                <div className="flex items-center space-x-1">
                  {onPreview && (
                    <button
                      onClick={() => onPreview(attachment.attachmentId)}
                      className="p-1.5 hover:bg-gray-100 rounded"
                      title="Preview"
                    >
                      <Eye className="h-4 w-4 text-gray-500" />
                    </button>
                  )}
                  {onDownload && (
                    <button
                      onClick={() => onDownload(attachment.attachmentId)}
                      className="p-1.5 hover:bg-gray-100 rounded"
                      title="Download"
                    >
                      <Download className="h-4 w-4 text-gray-500" />
                    </button>
                  )}
                  {onDelete && (
                    <button
                      onClick={() => handleDeleteExisting(attachment.attachmentId)}
                      className="p-1.5 hover:bg-red-50 rounded"
                      title="Delete"
                    >
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default AttachmentUploader;
