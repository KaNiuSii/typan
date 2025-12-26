# dev.ps1
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "./.venv\Scripts\Activate.ps1; mode con: cols=200 lines=60; textual run --dev run_app.py"
) -WindowStyle Maximized
