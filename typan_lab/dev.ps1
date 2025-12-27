# dev.ps1
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

Start-Process powershell -WindowStyle Maximized -ArgumentList @(
  "-NoExit",
  "-Command",
  @'
  cd "$PSScriptRoot"
  . ./.venv/Scripts/Activate.ps1

  $cols  = [Console]::WindowWidth
  $lines = [Console]::WindowHeight
  mode con: cols=$cols lines=$lines

  textual run --dev run_app.py
'@
)
