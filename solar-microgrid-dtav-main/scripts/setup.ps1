$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
python -m venv .venv
& .venv/Scripts/python -m pip install -r backend/requirements.txt -r scripts/requirements-docs.txt platformio==6.2.0
if ($LASTEXITCODE) { throw 'Python dependency installation failed' }
Push-Location frontend
try { npm.cmd ci; if ($LASTEXITCODE) { throw 'Frontend installation failed' } } finally { Pop-Location }
