$ErrorActionPreference = 'Stop'
$pythonCommand = (Get-Command python -ErrorAction Stop).Source
$pythonExecutable = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (!(Test-Path -LiteralPath $pythonExecutable)) {
    & $pythonCommand -m venv (Join-Path $PSScriptRoot '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
}
& $pythonExecutable -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Could not install pinned dependencies.' }
Write-Host 'Ready. Run start.ps1, then open http://127.0.0.1:8766.'
