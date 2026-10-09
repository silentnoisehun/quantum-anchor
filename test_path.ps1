$ErrorActionPreference = 'Stop'
Write-Host "Testing paths..."
Test-Path "C:\Users\mater\Documents\orassh\quantum_anchor"
Test-Path "C:\Users\mater\.minimax\workspace"
Get-ChildItem "C:\Users\mater\Documents\orassh\quantum_anchor" -ErrorAction SilentlyContinue
Get-ChildItem "C:\Users\mater\.minimax\workspace" -ErrorAction SilentlyContinue