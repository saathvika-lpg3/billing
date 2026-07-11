$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$LocalPython = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
$Candidates = @($LocalPython, $VenvPython)
$PathPython = Get-Command python -ErrorAction SilentlyContinue
if ($PathPython) {
    $Candidates += $PathPython.Source
}
$PythonExe = $null
foreach ($Candidate in $Candidates | Select-Object -Unique) {
    if (!(Test-Path $Candidate)) {
        continue
    }
    $PreviousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $Candidate -c "import PyInstaller" 2>$null
    $ImportExitCode = $LASTEXITCODE
    $ErrorActionPreference = $PreviousErrorActionPreference
    if ($ImportExitCode -eq 0) {
        $PythonExe = $Candidate
        break
    }
}
if (!$PythonExe) {
    throw "Python with PyInstaller was not found. Install PyInstaller in .venv or the local Python 3.13 runtime."
}
& $PythonExe "$Root\tools\prepare_installer_database.py" `
    --source "$Root\database\prm_billing_inventory.db" `
    --output "$Root\build\installer_payload\database\prm_billing_inventory.db" `
    --report "$Root\build\installer_payload\database\seed_report.json"
& $PythonExe -m PyInstaller --clean --noconfirm "$Root\PRM_Billing_Inventory.spec"
if (!(Test-Path "$Root\dist\PRM_Billing_Inventory\PRM_Billing_Inventory.exe")) {
    throw "PyInstaller completed without producing PRM_Billing_Inventory.exe"
}
