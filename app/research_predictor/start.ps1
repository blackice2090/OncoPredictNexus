param([int]$Port = 8766)
$ErrorActionPreference = 'Stop'
$projectDirectory = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$pythonExecutable = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (!(Test-Path -LiteralPath $pythonExecutable)) { throw 'Create the app Python environment using README_AR.md first.' }
Push-Location -LiteralPath $projectDirectory
try {
    Write-Host "Open http://127.0.0.1:$Port in your browser. Stop with Ctrl+C."
    & $pythonExecutable -X utf8 -m app.research_predictor.api --port $Port
    if ($LASTEXITCODE -ne 0) { throw 'OncoPredict prediction service did not start successfully.' }
} finally { Pop-Location }
