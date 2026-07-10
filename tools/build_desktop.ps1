$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
$Python = Get-Command python -ErrorAction SilentlyContinue
if ($Python) {
    $PythonExe = $Python.Source
} else {
    $PythonExe = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
}
if (!(Test-Path $PythonExe)) {
    throw "Python was not found. Install Python 3.13 or update tools\build_desktop.ps1 with the correct path."
}
& $PythonExe -m PyInstaller --clean --noconfirm "$Root\PRM_Billing_Inventory.spec"
