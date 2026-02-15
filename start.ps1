# Project Lend — single launcher
# Starts: Flask API, Vite frontend, and the pipeline (foreground)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $root "venv\Scripts\python.exe"
$frontendDir = Join-Path $root "frontend"

# ── 1. Flask API (background window) ────────────────────────
Write-Host "[*] Starting Flask API..." -ForegroundColor Cyan
Start-Process -FilePath $venvPython -ArgumentList (Join-Path $root "api.py") `
    -WorkingDirectory $root -WindowStyle Minimized

# ── 2. Frontend dev server (background window) ──────────────
Write-Host "[*] Starting frontend dev server..." -ForegroundColor Cyan
Start-Process -FilePath "cmd" -ArgumentList "/c","npm run dev" `
    -WorkingDirectory $frontendDir -WindowStyle Minimized

# Give servers a moment to boot
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "  Dashboard:  http://localhost:5173" -ForegroundColor Green
Write-Host "  API:        http://localhost:5000" -ForegroundColor Green
Write-Host ""

# ── 3. Pipeline (foreground — needs OpenCV window) ──────────
Write-Host "[*] Starting pipeline (press 'c' to classify, 'q' to quit)..." -ForegroundColor Cyan
& $venvPython (Join-Path $root "test_pipeline.py")

# ── Cleanup: kill background processes on exit ──────────────
Write-Host "[*] Shutting down background services..." -ForegroundColor Yellow
Get-Process -Name "python" -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -eq $venvPython } |
    Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name "node" -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue
Write-Host "[*] Done." -ForegroundColor Green
