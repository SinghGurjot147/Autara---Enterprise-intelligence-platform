param(
  [string]$ProjectRoot = "C:\Users\Asus\Desktop\minor project draft",
  [string]$FrontendRoot = "C:\Users\Asus\Desktop\frontend"
)

$ErrorActionPreference = "Stop"

$BackendRoot = Join-Path $ProjectRoot "backend"
$WorkspaceFile = Join-Path $FrontendRoot "src\components\workspace\workspace-views.tsx"
$ApiFile = Join-Path $FrontendRoot "src\services\api.ts"
$MainFile = Join-Path $BackendRoot "app\main.py"

Write-Host "Enterprise Intelligence Platform - Report Generator integration" -ForegroundColor Cyan
Write-Host "Backend:  $BackendRoot"
Write-Host "Frontend: $FrontendRoot"

$here = Split-Path -Parent $MyInvocation.MyCommand.Path

# --- Safety backups ---
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item $MainFile "$MainFile.reportgen-backup-$stamp" -ErrorAction SilentlyContinue
Copy-Item $WorkspaceFile "$WorkspaceFile.reportgen-backup-$stamp" -ErrorAction SilentlyContinue
Write-Host "Created timestamped backups for main.py and workspace-views.tsx" -ForegroundColor DarkGray

# --- Copy additive backend files ---
New-Item -ItemType Directory -Force -Path (Join-Path $BackendRoot "app\routers") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $BackendRoot "app\services") | Out-Null
Copy-Item (Join-Path $here "backend\app\routers\reports.py") (Join-Path $BackendRoot "app\routers\reports.py") -Force
Copy-Item (Join-Path $here "backend\app\services\report_generator.py") (Join-Path $BackendRoot "app\services\report_generator.py") -Force

# --- Add router to current main.py without replacing it ---
$main = Get-Content $MainFile -Raw
if ($main -notmatch 'backend\.app\.routers\.reports') {
  Add-Content -Path $MainFile -Value "`nfrom backend.app.routers.reports import router as reports_router`napp.include_router(reports_router)`n"
  Write-Host "Added reports router to backend main.py" -ForegroundColor Green
} else {
  Write-Host "Reports router already present; skipped" -ForegroundColor Yellow
}

# --- Copy additive frontend files ---
New-Item -ItemType Directory -Force -Path (Join-Path $FrontendRoot "src\components\workspace") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $FrontendRoot "src\services") | Out-Null
Copy-Item (Join-Path $here "frontend\src\components\workspace\report-generator.tsx") (Join-Path $FrontendRoot "src\components\workspace\report-generator.tsx") -Force
Copy-Item (Join-Path $here "frontend\src\services\report-api.ts") (Join-Path $FrontendRoot "src\services\report-api.ts") -Force

# --- Patch only the report section/import in workspace-views.tsx ---
$workspace = Get-Content $WorkspaceFile -Raw

if ($workspace -notmatch 'IntegratedReportGeneratorView') {
  $importAnchor = 'import type { UploadProgress } from "@/hooks/useDocuments"'
  if ($workspace -notmatch [regex]::Escape($importAnchor)) {
    throw "Could not find the expected workspace import anchor. No workspace changes were made."
  }
  $importLine = 'import { ReportGeneratorView as IntegratedReportGeneratorView } from "./report-generator"'
  $workspace = $workspace.Replace($importAnchor, $importAnchor + "`n" + $importLine)
}

$reportSection = '(?s)/\* =========================================================\s*3\. REPORT GENERATOR VIEW\s*========================================================= \*/.*?(?=/\* =========================================================\s*4\. PRESENTATION GENERATOR VIEW)'
if ($workspace -match $reportSection) {
  $replacement = @'
/* =========================================================
   3. REPORT GENERATOR VIEW
   ========================================================= */
// Implemented in ./report-generator.tsx to keep this workspace file small and
// preserve the existing presentation generator and other modules.

'@
  $workspace = [regex]::Replace($workspace, $reportSection, $replacement, 1)

  # These icons were used only by the old report card implementation.
  $workspace = $workspace -replace '(?m)^\s*FileSpreadsheet,\s*$', ''
  $workspace = $workspace -replace '(?m)^\s*ArrowRight,\s*$', ''
} else {
  throw "Could not find the Report Generator section. No workspace changes were made."
}

Set-Content -Path $WorkspaceFile -Value $workspace -Encoding UTF8

Write-Host "Report Generator integrated successfully." -ForegroundColor Green
Write-Host "Existing PPT generator and other workspace modules were left untouched." -ForegroundColor Green
Write-Host "Next: restart FastAPI on port 8001 and run the Vite frontend." -ForegroundColor Cyan
