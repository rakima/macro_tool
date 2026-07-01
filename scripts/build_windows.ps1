$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

python -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --name MacroTool `
  --distpath dist `
  --workpath build\pyinstaller `
  --specpath build `
  --hidden-import cv2 `
  app\gui_main.py

Write-Host "Built: dist\MacroTool\MacroTool.exe"
