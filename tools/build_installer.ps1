$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Iscc = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (!(Test-Path $Iscc)) {
    throw "Inno Setup compiler not found at $Iscc"
}
Set-Location $Root
$BuildStarted = Get-Date
& "$Root\tools\build_desktop.ps1"
if (!$?) {
    throw "Desktop build script failed"
}
& $Iscc "$Root\installer\prm_billing_inventory.iss"
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup failed with exit code $LASTEXITCODE"
}
$SetupExe = "$Root\installer_output\PRM_Billing_Inventory_Setup.exe"
if (!(Test-Path -LiteralPath $SetupExe)) {
    throw "Inno Setup completed without producing PRM_Billing_Inventory_Setup.exe"
}
if ((Get-Item -LiteralPath $SetupExe).LastWriteTime -lt $BuildStarted) {
    throw "Inno Setup left a stale PRM_Billing_Inventory_Setup.exe"
}
