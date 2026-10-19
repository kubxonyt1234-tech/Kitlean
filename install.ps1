$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
py -3.12 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "Wymagany Python 3.12 z tkinter." }
& .\.venv\Scripts\python.exe -m pip install -e ".[test]"
if ($LASTEXITCODE -ne 0) { throw "Instalacja nie powiodła się." }
Write-Host "Gotowe: .\.venv\Scripts\kitlean.exe run examples/clicker_03.kit"
