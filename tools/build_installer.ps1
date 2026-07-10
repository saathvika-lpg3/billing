$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Iscc = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (!(Test-Path $Iscc)) {
    throw "Inno Setup compiler not found at $Iscc"
}
Set-Location $Root
& "$Root\tools\build_desktop.ps1"
& $Iscc "$Root\installer\prm_billing_inventory.iss"
