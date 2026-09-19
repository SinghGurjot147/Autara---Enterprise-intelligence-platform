import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:5000';

export interface DocumentInfo {
  document_id: string;
  filename: string;
  size: number;
  content_type: string;
}

interface DocumentUploadResponse {
  document_id: string;
  filename: string;
}

interface DocumentListResponse {
  documents: DocumentInfo[];
}

export async function uploadDocument(
  file: File,
  onProgress?: (pct: number) => void,
): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await axios.post<DocumentUploadResponse>(
    `${API_BASE}/documents`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (event) => {
        if (onProgress && event.total) {
          onProgress(Math.round((event.loaded * 100) / event.total));
        }
      },
    },
  );
  return response.data;
}

export async function listDocuments(): Promise<DocumentListResponse> {
  const response = await axios.get<DocumentListResponse>(`${API_BASE}/documents`);
  return response.data;
}

export async function deleteDocument(documentId: string): Promise<void> {
  await axios.delete(`${API_BASE}/documents/${documentId}`);
}

export async function resetChatHistory(): Promise<void> {
  await axios.delete(`${API_BASE}/chat/history`);
}

export interface QueryResponse {
  answer: string;
  sources: {
    source: string;
    page: number | null;
  }[];
}

export async function queryRag(question: string): Promise<QueryResponse> {
  const response = await axios.post<QueryResponse>(
    `${API_BASE}/api/chat`,
    { question },
  );

  return response.data;
}

/* ---------------------------------------------------------------
   Presentation Generator
   Backend: presentations router (see backend/app/routers/presentations.py)
--------------------------------------------------------------- */

export type PresentationMode = 'general' | 'rag';
export type PresentationAudience = 'general' | 'student' | 'academic' | 'business' | 'technical';
export type PresentationTone = 'professional' | 'academic' | 'simple' | 'executive';
export type PresentationStyle = 'modern' | 'corporate' | 'academic' | 'minimal' | 'dark';

export interface PresentationRequest {
  topic: string;
  mode: PresentationMode;
  slide_count: number;
  audience: PresentationAudience;
  tone: PresentationTone;
  style: PresentationStyle;
  include_images: boolean;
  include_notes: boolean;
  include_sources: boolean;
  document_ids: string[];
}

export interface PresentationOutlineItem {
  slide_number: number;
  type: string;
  title: string;
}

export interface PresentationGenerateResponse {
  success: boolean;
  presentation_id: string;
  filename: string;
  download_url: string;
  slide_count: number;
  outline: PresentationOutlineItem[];
  warnings: string[];
}

export async function generatePresentation(
  req: PresentationRequest,
): Promise<PresentationGenerateResponse> {
  const response = await axios.post<PresentationGenerateResponse>(
    `${API_BASE}/presentations/generate`,
    req,
  );
  return response.data;
}

export function getPresentationDownloadUrl(downloadUrl: string): string {
  // downloadUrl comes back from the API as a relative path e.g. "/presentations/<id>/download"
  return `${API_BASE}${downloadUrl}`;
}
