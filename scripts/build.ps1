param([string]$SourceRom = "")
$ErrorActionPreference = "Stop"
Push-Location (Join-Path $PSScriptRoot "..")
try {
    if ($SourceRom) { python scripts/build_title.py --source $SourceRom }
    else { python scripts/build_title.py }
    if ($LASTEXITCODE -ne 0) { throw "Title build failed" }
} finally { Pop-Location }
