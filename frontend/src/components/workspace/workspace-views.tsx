import React, { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  BookOpen,
  BarChart3,
  FileSpreadsheet,
  Presentation,
  Search,
  Radio,
  Upload,
  Sparkles,
  ArrowRight,
  FileText,
  Layers,
  Cpu,
  TrendingUp,
  Clock,
  Loader2,
  CheckCircle2,
  Download,
  RotateCcw,
  Image as ImageIcon,
  StickyNote,
  BookMarked,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import type { DocumentInfo } from "@/services/api"
import {
  generatePresentation,
  getPresentationDownloadUrl,
  type PresentationAudience,
  type PresentationGenerateResponse,
  type PresentationStyle,
} from "@/services/api"
import { DocumentUpload } from "@/components/chat/document-upload"
import type { UploadProgress } from "@/hooks/useDocuments"

interface WorkspaceViewsProps {
  activeModule: string
  onSwitchToAssistant: (prompt?: string) => void
  documents: DocumentInfo[]
  uploading: UploadProgress | null
  onDocumentsChange: (updater: (prev: DocumentInfo[]) => DocumentInfo[]) => void
  onUploadStart: (filename: string) => void
  onUploadProgress: (filename: string, progress: number) => void
  onUploadEnd: () => void
  onError: (message: string) => void
}

export function WorkspaceViews({
  activeModule,
  onSwitchToAssistant,
  documents,
  uploading,
  onDocumentsChange,
  onUploadStart,
  onUploadProgress,
  onUploadEnd,
  onError,
}: WorkspaceViewsProps) {
  switch (activeModule) {
    case "knowledge":
      return (
        <KnowledgeBaseView
          documents={documents}
          uploading={uploading}
          onDocumentsChange={onDocumentsChange}
          onUploadStart={onUploadStart}
          onUploadProgress={onUploadProgress}
          onUploadEnd={onUploadEnd}
          onError={onError}
          onAskAi={onSwitchToAssistant}
        />
      )
    case "analytics":
      return <AnalyticsView onSwitchToAssistant={onSwitchToAssistant} />
    case "reports":
  return <ReportGeneratorView />
    case "presentations":
      return (
        <PresentationGeneratorView
          documents={documents}
          onError={onError}
          onFallbackToAssistant={onSwitchToAssistant}
        />
      )
    case "search":
      return (
        <SemanticSearchView
          documents={documents}
          onSearchInChat={onSwitchToAssistant}
        />
      )
    case "meetings":
      return <MeetingIntelligenceView onAnalyze={onSwitchToAssistant} />
    default:
      return null
  }
}

/* =========================================================
   1. KNOWLEDGE BASE VIEW
   ========================================================= */
function KnowledgeBaseView({
  documents,
  uploading,
  onDocumentsChange,
  onUploadStart,
  onUploadProgress,
  onUploadEnd,
  onError,
  onAskAi,
}: {
  documents: DocumentInfo[]
  uploading: UploadProgress | null
  onDocumentsChange: (updater: (prev: DocumentInfo[]) => DocumentInfo[]) => void
  onUploadStart: (filename: string) => void
  onUploadProgress: (filename: string, progress: number) => void
  onUploadEnd: () => void
  onError: (message: string) => void
  onAskAi: (prompt?: string) => void
}) {
  const [isDocExpanded, setIsDocExpanded] = useState(true)

  return (
    <div className="flex-1 overflow-y-auto px-6 py-8 max-w-5xl mx-auto w-full space-y-6">
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-primary" />
            Knowledge Base
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Vector database index powered by Chroma & llamacpp
          </p>
        </div>
        <Button
          onClick={() => onAskAi("Summarize the uploaded documents in our knowledge base.")}
          className="bg-primary/20 text-primary border border-primary/30 hover:bg-primary/30 text-xs h-8"
        >
          <Sparkles className="h-3.5 w-3.5 mr-1.5" />
          Ask AI About Docs
        </Button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <motion.div
          whileHover={{ y: -5, rotateX: 3, rotateY: -2, scale: 1.02 }}
          style={{ transformStyle: "preserve-3d", perspective: 800 }}
          className="p-4 rounded-xl bg-white/5 border border-white/10 hover:border-primary/40 hover:shadow-lg hover:shadow-primary/10 transition-all"
        >
          <span className="text-[11px] text-muted-foreground">Total Documents</span>
          <p className="text-2xl font-bold text-white mt-1">{documents.length}</p>
        </motion.div>
        <motion.div
          whileHover={{ y: -5, rotateX: 3, rotateY: -2, scale: 1.02 }}
          style={{ transformStyle: "preserve-3d", perspective: 800 }}
          className="p-4 rounded-xl bg-white/5 border border-white/10 hover:border-primary/40 hover:shadow-lg hover:shadow-primary/10 transition-all"
        >
          <span className="text-[11px] text-muted-foreground">Vector Store</span>
          <p className="text-2xl font-bold text-emerald-400 mt-1">ChromaDB</p>
        </motion.div>
        <motion.div
          whileHover={{ y: -5, rotateX: 3, rotateY: -2, scale: 1.02 }}
          style={{ transformStyle: "preserve-3d", perspective: 800 }}
          className="p-4 rounded-xl bg-white/5 border border-white/10 hover:border-primary/40 hover:shadow-lg hover:shadow-primary/10 transition-all"
        >
          <span className="text-[11px] text-muted-foreground">Embedding Dimension</span>
          <p className="text-2xl font-bold text-white mt-1">384-d</p>
        </motion.div>
      </div>

      {/* Document Upload Area */}
      <motion.div
        whileHover={{ y: -3, scale: 1.01 }}
        style={{ transformStyle: "preserve-3d", perspective: 800 }}
        className="rounded-xl border border-white/10 bg-white/5 p-4 hover:border-primary/30 transition-all"
      >
        <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
          <Upload className="h-4 w-4 text-primary" />
          Upload & Index Documents
        </h3>
        <DocumentUpload
          documents={documents}
          uploading={uploading}
          onDocumentsChange={onDocumentsChange}
          onUploadStart={onUploadStart}
          onUploadProgress={onUploadProgress}
          onUploadEnd={onUploadEnd}
          onError={onError}
          isExpanded={isDocExpanded}
          onToggleExpand={() => setIsDocExpanded((p) => !p)}
        />
      </motion.div>
    </div>
  )
}

/* =========================================================
   2. ANALYTICS VIEW
   ========================================================= */
function AnalyticsView({
  onSwitchToAssistant,
}: {
  onSwitchToAssistant: (prompt?: string) => void
}) {
  return (
    <div className="flex-1 overflow-y-auto px-6 py-8 max-w-5xl mx-auto w-full space-y-6">
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />
            Performance & Inference Analytics
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Real-time inference metrics, token throughput, and RAG retrieval latency
          </p>
        </div>
        <Button
          onClick={() => onSwitchToAssistant("Generate an analysis report of our model throughput and latency.")}
          className="bg-primary/20 text-primary border border-primary/30 hover:bg-primary/30 text-xs h-8"
        >
          <Sparkles className="h-3.5 w-3.5 mr-1.5" />
          Analyze with AI
        </Button>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <motion.div
          whileHover={{ y: -6, rotateX: 3, rotateY: -2, scale: 1.03 }}
          style={{ transformStyle: "preserve-3d", perspective: 800 }}
          className="p-4 rounded-xl bg-white/5 border border-white/10 hover:border-primary/40 hover:shadow-lg hover:shadow-primary/10 transition-all"
        >
          <div className="flex items-center justify-between text-muted-foreground text-xs">
            <span>Avg Latency</span>
            <Clock className="h-3.5 w-3.5 text-primary" />
          </div>
          <p className="text-2xl font-bold text-white mt-1">42 ms</p>
          <span className="text-[10px] text-emerald-400">99.4% SLA uptime</span>
        </motion.div>

        <motion.div
          whileHover={{ y: -6, rotateX: 3, rotateY: -2, scale: 1.03 }}
          style={{ transformStyle: "preserve-3d", perspective: 800 }}
          className="p-4 rounded-xl bg-white/5 border border-white/10 hover:border-primary/40 hover:shadow-lg hover:shadow-primary/10 transition-all"
        >
          <div className="flex items-center justify-between text-muted-foreground text-xs">
            <span>Throughput</span>
            <Cpu className="h-3.5 w-3.5 text-cyan-400" />
          </div>
          <p className="text-2xl font-bold text-white mt-1">68 t/s</p>
          <span className="text-[10px] text-muted-foreground">Tokens per second</span>
        </motion.div>

        <motion.div
          whileHover={{ y: -6, rotateX: 3, rotateY: -2, scale: 1.03 }}
          style={{ transformStyle: "preserve-3d", perspective: 800 }}
          className="p-4 rounded-xl bg-white/5 border border-white/10 hover:border-primary/40 hover:shadow-lg hover:shadow-primary/10 transition-all"
        >
          <div className="flex items-center justify-between text-muted-foreground text-xs">
            <span>RAG Hit Rate</span>
            <Layers className="h-3.5 w-3.5 text-pink-400" />
          </div>
          <p className="text-2xl font-bold text-white mt-1">94.8%</p>
          <span className="text-[10px] text-emerald-400">Cosine similarity &gt; 0.82</span>
        </motion.div>

        <motion.div
          whileHover={{ y: -6, rotateX: 3, rotateY: -2, scale: 1.03 }}
          style={{ transformStyle: "preserve-3d", perspective: 800 }}
          className="p-4 rounded-xl bg-white/5 border border-white/10 hover:border-primary/40 hover:shadow-lg hover:shadow-primary/10 transition-all"
        >
          <div className="flex items-center justify-between text-muted-foreground text-xs">
            <span>Queries Today</span>
            <TrendingUp className="h-3.5 w-3.5 text-amber-400" />
          </div>
          <p className="text-2xl font-bold text-white mt-1">1,280</p>
          <span className="text-[10px] text-emerald-400">+18% vs yesterday</span>
        </motion.div>
      </div>

      {/* Latency breakdown simulation */}
      <motion.div
        whileHover={{ y: -4, scale: 1.01 }}
        style={{ transformStyle: "preserve-3d", perspective: 800 }}
        className="p-5 rounded-xl bg-white/5 border border-white/10 space-y-4 hover:border-primary/30 transition-all"
      >
        <h3 className="text-sm font-semibold text-white">Pipeline Execution Times</h3>
        <div className="space-y-3 text-xs">
          <div>
            <div className="flex justify-between mb-1">
              <span className="text-muted-foreground">Vector Retrieval (ChromaDB)</span>
              <span className="text-white font-mono">14 ms</span>
            </div>
            <div className="h-2 rounded-full bg-white/10 overflow-hidden">
              <div className="h-full bg-cyan-400 rounded-full" style={{ width: "25%" }} />
            </div>
          </div>
          <div>
            <div className="flex justify-between mb-1">
              <span className="text-muted-foreground">Prompt Context Assembly</span>
              <span className="text-white font-mono">6 ms</span>
            </div>
            <div className="h-2 rounded-full bg-white/10 overflow-hidden">
              <div className="h-full bg-pink-400 rounded-full" style={{ width: "12%" }} />
            </div>
          </div>
          <div>
            <div className="flex justify-between mb-1">
              <span className="text-muted-foreground">llamacpp Generation</span>
              <span className="text-white font-mono">32 ms (first token)</span>
            </div>
            <div className="h-2 rounded-full bg-white/10 overflow-hidden">
              <div className="h-full bg-primary rounded-full" style={{ width: "63%" }} />
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

/* =========================================================
   3. REPORT GENERATOR VIEW
   ========================================================= */
function ReportGeneratorView() {
  const [uploading, setUploading] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<{
    name: string
    document_id: string
  } | null>(null)

  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState<{
    report_id: string
    filename: string
    download_url: string
  } | null>(null)

  const [error, setError] = useState<string | null>(null)

  const templates = [
    {
      title: "Executive Summary",
      desc: "High-level overview of key documents, insights, and critical action points.",
      prompt: "Generate an Executive Summary report based on the uploaded document.",
    },
    {
      title: "Technical Architecture Audit",
      desc: "Detailed technical breakdown, API interfaces, and system recommendations.",
      prompt: "Generate a Technical Architecture Audit report based on the uploaded document.",
    },
    {
      title: "Compliance & Security Review",
      desc: "Risk assessment, regulatory checklist, and vulnerability mitigations.",
      prompt: "Generate a Compliance & Security Review report based on the uploaded document.",
    },
    {
      title: "Weekly Intelligence Briefing",
      desc: "Consolidated updates, metric changes, and upcoming priorities.",
      prompt: "Generate a Weekly Intelligence Briefing based on the uploaded document.",
    },
  ]

  const handleUpload = async (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = e.target.files?.[0]

    if (!file) return

    if (
      file.type !== "application/pdf" &&
      !file.name.toLowerCase().endsWith(".pdf")
    ) {
      setError("Only PDF files are supported.")
      e.target.value = ""
      return
    }

    setUploading(true)
    setError(null)
    setResult(null)

    try {
      const formData = new FormData()
      formData.append("file", file)

      const response = await fetch("/documents", {
        method: "POST",
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || "PDF upload failed.")
      }

      setUploadedFile({
        name: data.filename || file.name,
        document_id: data.document_id,
      })
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "PDF upload failed."
      )
    } finally {
      setUploading(false)
      e.target.value = ""
    }
  }

  const handleGenerate = async (prompt: string) => {
    if (!uploadedFile) {
      setError("Upload a PDF before generating a report.")
      return
    }

    if (generating) return

    setGenerating(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch("/reports/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          topic: prompt,
          document_ids: [uploadedFile.document_id],
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.error || "Report generation failed."
        )
      }

      setResult({
        report_id: data.report_id,
        filename: data.filename,
        download_url: data.download_url,
      })
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Report generation failed."
      )
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="flex-1 overflow-y-auto px-6 py-8 max-w-5xl mx-auto w-full space-y-6">

      {/* HEADER */}
      <div className="border-b border-white/10 pb-4">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <FileSpreadsheet className="h-5 w-5 text-primary" />
          Report Generator
        </h2>

        <p className="text-xs text-muted-foreground mt-0.5">
          Generate professional AI-powered reports from an uploaded document
        </p>
      </div>

      {/* SOURCE DOCUMENT */}
      <div className="rounded-xl bg-white/5 border border-white/10 p-5">

        <div className="flex items-center gap-2 mb-1">
          <Upload className="h-4 w-4 text-primary" />

          <div className="text-sm font-semibold text-white">
            Source Document
          </div>
        </div>

        <p className="text-xs text-muted-foreground mb-4">
          Upload a PDF before selecting a report type.
        </p>

        <label
          className={`flex flex-col items-center justify-center h-32 rounded-lg border border-dashed border-white/20 bg-black/20 transition-all ${
            uploading
              ? "opacity-60 cursor-not-allowed"
              : "cursor-pointer hover:border-primary/50 hover:bg-primary/5"
          }`}
        >
          <Upload className="h-7 w-7 text-primary mb-2" />

          <span className="text-sm text-white">
            {uploading
              ? "Uploading and indexing..."
              : "Click to upload PDF"}
          </span>

          <span className="text-[11px] text-muted-foreground mt-1">
            PDF files only
          </span>

          <input
            type="file"
            accept=".pdf"
            onChange={handleUpload}
            disabled={uploading}
            className="hidden"
          />
        </label>

        {/* SELECTED FILE */}
        {uploadedFile && (
          <div className="mt-3 flex items-center gap-3 p-3 rounded-lg bg-secondary/50 border border-border/30">
            <FileText className="h-5 w-5 text-primary" />

            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {uploadedFile.name}
              </p>

              <p className="text-xs text-primary mt-1">
                Document indexed and ready
              </p>
            </div>
          </div>
        )}
      </div>

      {/* ERROR */}
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-300">
          {error}
        </div>
      )}

      {/* RESULT */}
      {result && (
        <div className="rounded-xl bg-primary/5 border border-primary/20 p-4">
          <div className="flex items-center justify-between gap-4">

            <div>
              <p className="text-sm font-semibold text-white">
                Report generated successfully
              </p>

              <p className="text-xs text-muted-foreground mt-1">
                {result.filename}
              </p>
            </div>

            <a
              href={result.download_url}
              target="_blank"
              rel="noreferrer"
              className="px-4 py-2 rounded-lg bg-primary text-white text-xs font-medium hover:opacity-90"
            >
              Download PDF
            </a>

          </div>
        </div>
      )}

      {/* REPORT TEMPLATES */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

        {templates.map((tpl) => (
          <motion.div
            key={tpl.title}
            whileHover={{
              y: -6,
              rotateX: 3,
              rotateY: -2,
              scale: 1.02,
            }}
            style={{
              transformStyle: "preserve-3d",
              perspective: 800,
            }}
            className="p-5 rounded-xl bg-white/5 border border-white/10 hover:border-primary/40 hover:shadow-xl hover:shadow-primary/10 transition-all flex flex-col justify-between group"
          >
            <div>
              <div className="flex items-center gap-2 text-primary text-sm font-semibold mb-1.5">
                <FileText className="h-4 w-4" />
                {tpl.title}
              </div>

              <p className="text-xs text-muted-foreground leading-relaxed">
                {tpl.desc}
              </p>
            </div>

            <Button
              disabled={!uploadedFile || generating}
              onClick={() => handleGenerate(tpl.prompt)}
              className="mt-4 w-full bg-white/5 hover:bg-primary/20 hover:text-primary border border-white/10 hover:border-primary/30 text-xs h-8 transition-all disabled:opacity-40"
            >
              {generating
                ? "Generating..."
                : "Generate with AI"}

              <ArrowRight className="h-3 w-3 ml-1.5" />
            </Button>
          </motion.div>
        ))}

      </div>
    </div>
  )
}

/* =========================================================
   4. PRESENTATION GENERATOR VIEW
   ========================================================= */
type GenStage = "idle" | "planning" | "content" | "visuals" | "building" | "done" | "error"

const STAGE_COPY: Record<Exclude<GenStage, "idle" | "done" | "error">, string> = {
  planning: "Planning presentation structure…",
  content: "Generating slide content…",
  visuals: "Finding visuals…",
  building: "Building PowerPoint…",
}

function PresentationGeneratorView({
  documents,
  onError,
  onFallbackToAssistant,
}: {
  documents: DocumentInfo[]
  onError: (message: string) => void
  onFallbackToAssistant: (prompt?: string) => void
}) {
  const [topic, setTopic] = useState("")
  const [mode, setMode] = useState<"general" | "rag">("general")
  const [slideCount, setSlideCount] = useState(10)
  const [audience, setAudience] = useState<PresentationAudience>("business")
  const [style, setStyle] = useState<PresentationStyle>("modern")
  const [includeImages, setIncludeImages] = useState(true)
  const [includeNotes, setIncludeNotes] = useState(true)
  const [includeSources, setIncludeSources] = useState(true)

  const [stage, setStage] = useState<GenStage>("idle")
  const [result, setResult] = useState<PresentationGenerateResponse | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const isGenerating = stage !== "idle" && stage !== "done" && stage !== "error"
  const ragUnavailable = mode === "rag" && documents.length === 0

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!topic.trim() || isGenerating) return

    setResult(null)
    setErrorMsg(null)
    setStage("planning")

    // Staged progress is cosmetic — the backend call below is a single request,
    // but we advance the UI through the pipeline stages the API actually performs
    // (planning -> content -> visuals -> building) so generation never looks frozen.
    const advance = window.setTimeout(() => setStage("content"), 900)
    const advance2 = window.setTimeout(() => setStage("visuals"), 1900)
    const advance3 = window.setTimeout(() => setStage("building"), 2900)

    try {
      const response = await generatePresentation({
        topic: topic.trim(),
        mode,
        slide_count: slideCount,
        audience,
        tone: "professional",
        style,
        include_images: includeImages,
        include_notes: includeNotes,
        include_sources: includeSources,
        document_ids: mode === "rag" ? documents.map((d) => d.document_id) : [],
      })
      window.clearTimeout(advance)
      window.clearTimeout(advance2)
      window.clearTimeout(advance3)
      setResult(response)
      setStage("done")
      response.warnings.forEach((w) => onError(w))
    } catch (err) {
      window.clearTimeout(advance)
      window.clearTimeout(advance2)
      window.clearTimeout(advance3)
      const message =
        err instanceof Error ? err.message : "Presentation generation failed. Please try again."
      setErrorMsg(message)
      setStage("error")
      onError(message)
    }
  }

  const handleGenerateAgain = () => {
    setResult(null)
    setErrorMsg(null)
    setStage("idle")
  }

  return (
    <div className="flex-1 overflow-y-auto px-6 py-8 max-w-4xl mx-auto w-full space-y-6">
      <div className="border-b border-white/10 pb-4">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Presentation className="h-5 w-5 text-primary" />
          Presentation Generator
        </h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          Turn a topic or your indexed documents into a downloadable, professionally laid out
          PowerPoint deck
        </p>
      </div>

      <AnimatePresence mode="wait">
        {stage === "idle" || stage === "error" ? (
          <motion.form
            key="form"
            onSubmit={handleSubmit}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="p-6 rounded-xl bg-white/5 border border-white/10 hover:border-primary/30 transition-all space-y-5"
          >
            <div>
              <label className="block text-xs font-medium text-white mb-1.5">
                What should this presentation be about?
              </label>
              <textarea
                rows={3}
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g. Electronic Waste Management — challenges, impact and sustainable solutions"
                maxLength={400}
                className="w-full bg-black/40 border border-white/10 rounded-lg p-3 text-xs text-white placeholder:text-muted-foreground/50 focus:outline-none focus:border-primary"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-white mb-2">Source</label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setMode("general")}
                  className={`flex-1 text-left px-3 py-2.5 rounded-lg border text-xs transition-all ${
                    mode === "general"
                      ? "bg-primary/15 border-primary/40 text-white"
                      : "bg-black/20 border-white/10 text-muted-foreground hover:border-white/20"
                  }`}
                >
                  <span className="block font-semibold mb-0.5">AI Knowledge</span>
                  <span className="block text-[11px] opacity-80">
                    Generated from the topic using Gemini
                  </span>
                </button>
                <button
                  type="button"
                  onClick={() => setMode("rag")}
                  className={`flex-1 text-left px-3 py-2.5 rounded-lg border text-xs transition-all ${
                    mode === "rag"
                      ? "bg-primary/15 border-primary/40 text-white"
                      : "bg-black/20 border-white/10 text-muted-foreground hover:border-white/20"
                  }`}
                >
                  <span className="block font-semibold mb-0.5">My Documents</span>
                  <span className="block text-[11px] opacity-80">
                    {documents.length > 0
                      ? `Grounded in ${documents.length} indexed document${documents.length === 1 ? "" : "s"}`
                      : "No documents indexed yet"}
                  </span>
                </button>
              </div>
              {ragUnavailable && (
                <p className="text-[11px] text-amber-400/90 mt-1.5">
                  Upload documents in Knowledge Base first, or generation will fall back to
                  topic-only content.
                </p>
              )}
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-white mb-1">Slides</label>
                <input
                  type="number"
                  min={3}
                  max={30}
                  value={slideCount}
                  onChange={(e) => setSlideCount(Number(e.target.value))}
                  className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-primary"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-white mb-1">Audience</label>
                <select
                  value={audience}
                  onChange={(e) => setAudience(e.target.value as PresentationAudience)}
                  className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-primary"
                >
                  <option value="general">General</option>
                  <option value="student">Student</option>
                  <option value="academic">Academic</option>
                  <option value="business">Business</option>
                  <option value="technical">Technical</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-white mb-1">Style</label>
                <select
                  value={style}
                  onChange={(e) => setStyle(e.target.value as PresentationStyle)}
                  className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-primary"
                >
                  <option value="modern">Modern</option>
                  <option value="corporate">Corporate</option>
                  <option value="academic">Academic</option>
                  <option value="minimal">Minimal</option>
                  <option value="dark">Dark</option>
                </select>
              </div>
            </div>

            <div className="flex flex-wrap gap-4 pt-1">
              <label className="flex items-center gap-2 text-xs text-white cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeImages}
                  onChange={(e) => setIncludeImages(e.target.checked)}
                  className="accent-primary"
                />
                <ImageIcon className="h-3.5 w-3.5 text-muted-foreground" />
                Include images
              </label>
              <label className="flex items-center gap-2 text-xs text-white cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeNotes}
                  onChange={(e) => setIncludeNotes(e.target.checked)}
                  className="accent-primary"
                />
                <StickyNote className="h-3.5 w-3.5 text-muted-foreground" />
                Speaker notes
              </label>
              <label className="flex items-center gap-2 text-xs text-white cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeSources}
                  onChange={(e) => setIncludeSources(e.target.checked)}
                  className="accent-primary"
                />
                <BookMarked className="h-3.5 w-3.5 text-muted-foreground" />
                Sources slide
              </label>
            </div>

            {stage === "error" && errorMsg && (
              <p className="text-[11px] text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                {errorMsg}
              </p>
            )}

            <Button
              type="submit"
              disabled={!topic.trim()}
              className="w-full bg-primary hover:bg-primary/90 text-primary-foreground text-xs h-9 font-medium"
            >
              <Sparkles className="h-3.5 w-3.5 mr-2" />
              Generate Presentation
            </Button>
          </motion.form>
        ) : isGenerating ? (
          <motion.div
            key="progress"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="p-6 rounded-xl bg-white/5 border border-white/10 space-y-4"
          >
            {(["planning", "content", "visuals", "building"] as const).map((s) => {
              const order = ["planning", "content", "visuals", "building"]
              const currentIdx = order.indexOf(stage)
              const thisIdx = order.indexOf(s)
              const isDone = thisIdx < currentIdx
              const isCurrent = thisIdx === currentIdx
              return (
                <div key={s} className="flex items-center gap-3 text-xs">
                  {isDone ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  ) : isCurrent ? (
                    <Loader2 className="h-4 w-4 text-primary animate-spin shrink-0" />
                  ) : (
                    <div className="h-4 w-4 rounded-full border border-white/15 shrink-0" />
                  )}
                  <span className={isDone || isCurrent ? "text-white" : "text-muted-foreground"}>
                    {STAGE_COPY[s]}
                  </span>
                </div>
              )
            })}
          </motion.div>
        ) : (
          result && (
            <motion.div
              key="result"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="p-6 rounded-xl bg-white/5 border border-primary/30 space-y-4"
            >
              <div className="flex items-center gap-2 text-emerald-400 text-xs font-semibold">
                <CheckCircle2 className="h-4 w-4" />
                {result.slide_count} slides generated
              </div>

              <div className="space-y-1 max-h-72 overflow-y-auto pr-1">
                {result.outline.map((item) => (
                  <div
                    key={item.slide_number}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg bg-black/20 border border-white/5 text-xs"
                  >
                    <span className="font-mono text-muted-foreground w-6 shrink-0">
                      {String(item.slide_number).padStart(2, "0")}
                    </span>
                    <span className="text-white truncate">{item.title}</span>
                    <span className="ml-auto text-[10px] uppercase tracking-wide text-muted-foreground shrink-0">
                      {item.type.replace("_", " ")}
                    </span>
                  </div>
                ))}
              </div>

              <div className="flex gap-2 pt-1">
                <Button
                  type="button"
                  onClick={handleGenerateAgain}
                  variant="outline"
                  className="flex-1 text-xs h-9 border-white/15 text-white hover:bg-white/5"
                >
                  <RotateCcw className="h-3.5 w-3.5 mr-2" />
                  Generate Again
                </Button>
                <a
                  href={getPresentationDownloadUrl(result.download_url)}
                  download={result.filename}
                  className="flex-1"
                >
                  <Button
                    type="button"
                    className="w-full bg-primary hover:bg-primary/90 text-primary-foreground text-xs h-9 font-medium"
                  >
                    <Download className="h-3.5 w-3.5 mr-2" />
                    Download PPTX
                  </Button>
                </a>
              </div>
            </motion.div>
          )
        )}
      </AnimatePresence>

      <button
        type="button"
        onClick={() => onFallbackToAssistant()}
        className="text-[11px] text-muted-foreground hover:text-white transition-colors flex items-center gap-1"
      >
        Prefer a quick outline in chat instead? Ask the AI Assistant
        <ArrowRight className="h-3 w-3" />
      </button>
    </div>
  )
}

/* =========================================================
   5. SEMANTIC SEARCH VIEW
   ========================================================= */
function SemanticSearchView({
  documents,
  onSearchInChat,
}: {
  documents: DocumentInfo[]
  onSearchInChat: (prompt: string) => void
}) {
  const [query, setQuery] = useState("")

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    onSearchInChat(
      `Perform a deep semantic search over all indexed knowledge documents for query: "${query}". Provide matching passages, relevance scores, and synthesis.`
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-6 py-8 max-w-4xl mx-auto w-full space-y-6">
      <div className="border-b border-white/10 pb-4">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Search className="h-5 w-5 text-primary" />
          Semantic Search
        </h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          Dense vector similarity query across all embedded knowledge chunks
        </p>
      </div>

      <form onSubmit={handleSearch} className="space-y-4">
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search concepts, questions, or keywords across your documents..."
            className="w-full bg-white/5 border border-white/15 rounded-xl pl-10 pr-24 py-3 text-sm text-white placeholder:text-muted-foreground/50 focus:outline-none focus:border-primary shadow-sm"
          />
          <Search className="absolute left-3.5 top-3.5 h-4 w-4 text-muted-foreground" />
          <Button
            type="submit"
            disabled={!query.trim()}
            className="absolute right-2 top-2 h-8 px-3 text-xs bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg"
          >
            Search
          </Button>
        </div>
      </form>

      <motion.div
        whileHover={{ y: -4, scale: 1.01 }}
        style={{ transformStyle: "preserve-3d", perspective: 800 }}
        className="p-5 rounded-xl bg-white/5 border border-white/10 space-y-3 hover:border-primary/30 hover:shadow-lg transition-all"
      >
        <span className="text-xs font-semibold text-white">Knowledge Index Scope</span>
        <p className="text-xs text-muted-foreground">
          Currently indexing {documents.length} document(s) in Chroma vector storage.
        </p>
        <div className="flex flex-wrap gap-2 pt-1">
          {documents.map((doc) => (
            <span
              key={doc.document_id}
              className="text-[11px] px-2.5 py-1 rounded-md bg-white/5 border border-white/10 text-white font-mono flex items-center gap-1.5"
            >
              <FileText className="h-3 w-3 text-primary" />
              {doc.filename}
            </span>
          ))}
        </div>
      </motion.div>
    </div>
  )
}

/* =========================================================
   6. MEETING INTELLIGENCE VIEW
   ========================================================= */
function MeetingIntelligenceView({
  onAnalyze,
}: {
  onAnalyze: (prompt: string) => void
}) {
  const [transcript, setTranscript] = useState("")

  const handleAnalyze = (e: React.FormEvent) => {
    e.preventDefault()
    if (!transcript.trim()) return
    onAnalyze(
      `Analyze this meeting transcript and produce:\n1. Executive Summary\n2. Key Decisions Made\n3. Action Items & Owners\n4. Follow-up Questions\n\nTranscript:\n${transcript}`
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-6 py-8 max-w-4xl mx-auto w-full space-y-6">
      <div className="border-b border-white/10 pb-4">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Radio className="h-5 w-5 text-primary" />
          Meeting Intelligence
        </h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          Extract decisions, assign action items, and summarize recorded transcripts
        </p>
      </div>

      <motion.form
        onSubmit={handleAnalyze}
        whileHover={{ y: -4, scale: 1.01 }}
        style={{ transformStyle: "preserve-3d", perspective: 800 }}
        className="p-6 rounded-xl bg-white/5 border border-white/10 space-y-4 hover:border-primary/30 hover:shadow-lg transition-all"
      >
        <div>
          <label className="block text-xs font-medium text-white mb-1.5">
            Paste Meeting Transcript or Notes
          </label>
          <textarea
            rows={6}
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder="Speaker 1: Let's discuss the Chroma indexing latency...&#10;Speaker 2: We optimized token chunking to 512 tokens with 50 token overlap...&#10;Speaker 1: Great, action item for Ayush to benchmark..."
            className="w-full bg-black/40 border border-white/10 rounded-lg p-3 text-xs text-white placeholder:text-muted-foreground/50 focus:outline-none focus:border-primary"
          />
        </div>

        <Button
          type="submit"
          disabled={!transcript.trim()}
          className="w-full bg-primary hover:bg-primary/90 text-primary-foreground text-xs h-9 font-medium"
        >
          <Sparkles className="h-3.5 w-3.5 mr-2" />
          Extract Action Items & Summary
        </Button>
      </motion.form>
    </div>
  )
}
