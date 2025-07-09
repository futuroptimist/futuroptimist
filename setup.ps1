<#
setup.ps1 – Windows helper to bootstrap dev environment
Usage:
  powershell -ExecutionPolicy Bypass -File .\setup.ps1 [-Test] [-Subtitles]
#>
param(
    [switch]$Test,
    [switch]$Subtitles
)

$venv = ".venv"
if (-not (Test-Path $venv)) {
    Write-Host "Creating virtual environment..."
    python -m venv $venv
}

$python = Join-Path $venv "Scripts/python.exe"
Write-Host "Installing requirements with uv..."
uv pip install -r requirements.txt | Out-Null

if ($Test) {
    Write-Host "Running tests..."
    & $python -m pytest -q
}

if ($Subtitles) {
    Write-Host "Fetching subtitles..."
    & $python src/fetch_subtitles.py
}

Write-Host "Setup complete. Activate with: `n .\.venv\Scripts\Activate.ps1"
