import axios from "axios"

const API_BASE = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8001"

export type ReportType =
  | "executive_summary"
  | "technical_architecture_audit"
  | "compliance_security_review"
  | "weekly_intelligence_briefing"

export interface GenerateReportRequest {
  report_type: ReportType
  document_ids: string[]
}

export interface GenerateReportResponse {
  report_id: string
  report_type: ReportType
  title: string
  markdown: string
  download_url: string
  pdf_filename: string
  markdown_filename: string
  sources: { label: string; document: string; page: number | null }[]
  provider: string
  warnings: string[]
}

export async function generateReport(
  request: GenerateReportRequest,
): Promise<GenerateReportResponse> {
  const response = await axios.post<GenerateReportResponse>(
    `${API_BASE}/reports/generate`,
    request,
  )
  return response.data
}

export function getReportDownloadUrl(downloadUrl: string): string {
  if (/^https?:\/\//i.test(downloadUrl)) return downloadUrl
  return `${API_BASE}${downloadUrl}`
}
