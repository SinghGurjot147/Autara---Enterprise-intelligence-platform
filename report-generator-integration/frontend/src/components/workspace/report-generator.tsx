import React, { useRef, useState } from "react"
import { motion } from "framer-motion"
import {
  ArrowRight,
  CheckCircle2,
  Download,
  FileText,
  FileUp,
  Loader2,
  X,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import type { DocumentInfo } from "@/services/api"
import { listDocuments, uploadDocument } from "@/services/api"
import {
  generateReport,
  getReportDownloadUrl,
  type GenerateReportResponse,
  type ReportType,
} from "@/services/report-api"

interface ReportGeneratorViewProps {
  documents: DocumentInfo[]
  onDocumentsChange?: (updater: (prev: DocumentInfo[]) => DocumentInfo[]) => void
  onError?: (message: string) => void
}

type ReportTemplate = {
  type: ReportType
  title: string
  desc: string
  approach: string
}

const templates: ReportTemplate[] = [
  {
    type: "executive_summary",
    title: "Executive Summary",
    desc: "High-level overview of key documents, insights, and critical action points.",
    approach: "Synthesizes the most important findings, decisions, risks, and actions.",
  },
  {
    type: "technical_architecture_audit",
    title: "Technical Architecture Audit",
    desc: "Detailed technical breakdown, API interfaces, and system recommendations.",
    approach: "Examines architecture, components, interfaces, dependencies, risks, and improvements.",
  },
  {
    type: "compliance_security_review",
    title: "Compliance & Security Review",
    desc: "Risk assessment, regulatory checklist, and vulnerability mitigations.",
    approach: "Extracts evidence, controls, gaps, risks, and document-grounded mitigations.",
  },
  {
    type: "weekly_intelligence_briefing",
    title: "Weekly Intelligence Briefing",
    desc: "Consolidated updates, metric changes, and upcoming priorities.",
    approach: "Turns the selected material into highlights, changes, risks, and priorities.",
  },
]

function mergeDocuments(
  setDocuments: ReportGeneratorViewProps["onDocumentsChange"],
): void {
  if (!setDocuments) return
  void listDocuments().then((result) => {
    setDocuments(() => result.documents)
  })
}

function ReportCard({
  template,
  documents,
  onDocumentsChange,
  onError,
}: {
  template: ReportTemplate
  documents: DocumentInfo[]
  onDocumentsChange?: ReportGeneratorViewProps["onDocumentsChange"]
  onError?: (message: string) => void
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [localFiles, setLocalFiles] = useState<string[]>([])
  const [uploading, setUploading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState<GenerateReportResponse | null>(null)
  const [error, setError] = useState("")

  const selectedDocs = documents.filter((doc) => selectedIds.includes(doc.document_id))

  const addUploadedIds = (ids: string[]) => {
    setSelectedIds((prev) => [...new Set([...prev, ...ids])])
  }

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? [])
    if (!files.length) return

    setUploading(true)
    setError("")
    try {
      const uploadedIds: string[] = []
      for (const file of files) {
        const uploaded = await uploadDocument(file)
        uploadedIds.push(uploaded.document_id)
      }
      setLocalFiles((prev) => [...prev, ...files.map((file) => file.name)])
      addUploadedIds(uploadedIds)
      mergeDocuments(onDocumentsChange)
    } catch (err) {
      const message = err instanceof Error ? err.message : "Document upload failed."
      setError(message)
      onError?.(message)
    } finally {
      setUploading(false)
      event.target.value = ""
    }
  }

  const handleGenerate = async () => {
    if (!selectedIds.length) {
      setError("Upload or select at least one document first.")
      return
    }

    setGenerating(true)
    setError("")
    setResult(null)
    try {
      const response = await generateReport({
        report_type: template.type,
        document_ids: selectedIds,
      })
      setResult(response)
    } catch (err: any) {
      const message =
        err?.response?.data?.detail ||
        err?.message ||
        "Report generation failed."
      setError(message)
      onError?.(message)
    } finally {
      setGenerating(false)
    }
  }

  const toggleExisting = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((value) => value !== id) : [...prev, id],
    )
  }

  return (
    <motion.div
      whileHover={{ y: -4, scale: 1.005 }}
      style={{ transformStyle: "preserve-3d", perspective: 800 }}
      className="p-5 rounded-xl bg-white/5 border border-white/10 hover:border-primary/40 hover:shadow-xl hover:shadow-primary/10 transition-all flex flex-col gap-4"
    >
      <div>
        <div className="flex items-center gap-2 text-primary text-sm font-semibold mb-1.5">
          <FileText className="h-4 w-4" />
          {template.title}
        </div>
        <p className="text-xs text-muted-foreground leading-relaxed">{template.desc}</p>
        <p className="text-[11px] text-muted-foreground/70 mt-2">{template.approach}</p>
      </div>

      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".pdf"
        className="hidden"
        onChange={handleUpload}
      />

      <Button
        type="button"
        variant="outline"
        disabled={uploading || generating}
        onClick={() => inputRef.current?.click()}
        className="w-full border-white/10 bg-white/5 hover:bg-primary/10 hover:text-primary text-xs h-9"
      >
        {uploading ? (
          <Loader2 className="h-3.5 w-3.5 mr-2 animate-spin" />
        ) : (
          <FileUp className="h-3.5 w-3.5 mr-2" />
        )}
        {uploading ? "Uploading documents..." : "Upload Documents"}
      </Button>

      {localFiles.length > 0 && (
        <div className="space-y-1">
          {localFiles.map((name, index) => (
            <div
              key={`${name}-${index}`}
              className="flex items-center gap-2 text-[11px] text-muted-foreground bg-black/30 rounded-md px-2.5 py-1.5"
            >
              <CheckCircle2 className="h-3 w-3 text-emerald-400 shrink-0" />
              <span className="truncate">{name}</span>
            </div>
          ))}
        </div>
      )}

      {documents.length > 0 && (
        <div className="border-t border-white/10 pt-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] text-muted-foreground">Use existing documents</span>
            {selectedIds.length > 0 && (
              <span className="text-[10px] text-primary">{selectedIds.length} selected</span>
            )}
          </div>
          <div className="max-h-28 overflow-y-auto space-y-1 pr-1">
            {documents.map((doc) => {
              const checked = selectedIds.includes(doc.document_id)
              return (
                <button
                  type="button"
                  key={doc.document_id}
                  onClick={() => toggleExisting(doc.document_id)}
                  className={`w-full flex items-center gap-2 text-left text-[11px] rounded-md px-2 py-1.5 transition-all ${
                    checked
                      ? "bg-primary/10 text-primary border border-primary/20"
                      : "bg-black/20 text-muted-foreground hover:bg-white/5"
                  }`}
                >
                  <span
                    className={`h-3 w-3 rounded border shrink-0 ${
                      checked ? "bg-primary border-primary" : "border-white/20"
                    }`}
                  />
                  <span className="truncate">{doc.filename}</span>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {selectedDocs.length > 0 && (
        <div className="text-[10px] text-muted-foreground">
          {selectedDocs.length} document{selectedDocs.length === 1 ? "" : "s"} will be analyzed.
        </div>
      )}

      {error && (
        <div className="text-[11px] text-red-300 bg-red-500/10 border border-red-500/20 rounded-md px-3 py-2">
          {error}
        </div>
      )}

      <Button
        type="button"
        disabled={uploading || generating || !selectedIds.length}
        onClick={handleGenerate}
        className="w-full bg-white/5 hover:bg-primary/20 hover:text-primary border border-white/10 hover:border-primary/30 text-xs h-9 transition-all"
      >
        {generating ? (
          <Loader2 className="h-3.5 w-3.5 mr-2 animate-spin" />
        ) : (
          <ArrowRight className="h-3.5 w-3.5 mr-2" />
        )}
        {generating ? "Generating report..." : "Generate with AI"}
      </Button>

      {result && (
        <div className="border-t border-white/10 pt-4 space-y-3">
          <div className="flex items-center gap-2 text-emerald-400 text-xs font-medium">
            <CheckCircle2 className="h-4 w-4" />
            Report generated with {result.provider}
          </div>
          <div className="bg-black/30 rounded-lg border border-white/10 p-3 max-h-48 overflow-y-auto">
            <pre className="whitespace-pre-wrap font-sans text-[11px] leading-relaxed text-muted-foreground">
              {result.markdown}
            </pre>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <a
              href={getReportDownloadUrl(result.download_url)}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center justify-center rounded-md border border-primary/30 bg-primary/10 text-primary text-xs h-9 hover:bg-primary/20 transition-all"
            >
              <Download className="h-3.5 w-3.5 mr-2" />
              Download PDF
            </a>
            <button
              type="button"
              onClick={() => setResult(null)}
              className="inline-flex items-center justify-center rounded-md border border-white/10 bg-white/5 text-muted-foreground text-xs h-9 hover:bg-white/10 transition-all"
            >
              <X className="h-3.5 w-3.5 mr-2" />
              Close Result
            </button>
          </div>
        </div>
      )}
    </motion.div>
  )
}

export function ReportGeneratorView({
  documents,
  onDocumentsChange,
  onError,
}: ReportGeneratorViewProps) {
  return (
    <div className="flex-1 overflow-y-auto px-6 py-8 max-w-5xl mx-auto w-full space-y-6">
      <div className="border-b border-white/10 pb-4">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <FileText className="h-5 w-5 text-primary" />
          Report Generator
        </h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          Upload documents and generate focused multi-page reports with source citations
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {templates.map((template) => (
          <ReportCard
            key={template.type}
            template={template}
            documents={documents}
            onDocumentsChange={onDocumentsChange}
            onError={onError}
          />
        ))}
      </div>
    </div>
  )
}
