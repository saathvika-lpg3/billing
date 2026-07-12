$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Iscc = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (!(Test-Path $Iscc)) {
    throw "Inno Setup compiler not found at $Iscc"
}
Set-Location $Root
$BuildStarted = Get-Date
# Internal 1.7.8 used the legacy unversioned setup filename. The official V1.0
# build writes a different filename and must never delete or overwrite that
# last-known-good prerelease artifact while validating the semantic reset.
$InternalPrereleaseSetup = "$Root\installer_output\PRM_Billing_Inventory_Setup.exe"
$InternalPrereleaseHash = $null
if (Test-Path -LiteralPath $InternalPrereleaseSetup) {
    $InternalPrereleaseHash = (Get-FileHash -LiteralPath $InternalPrereleaseSetup -Algorithm SHA256).Hash
}
& "$Root\tools\build_desktop.ps1"
if (!$?) {
    throw "Desktop build script failed"
}
& $Iscc "$Root\installer\prm_billing_inventory.iss"
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup failed with exit code $LASTEXITCODE"
}
$SetupExe = "$Root\installer_output\PRM_Billing_Inventory_V1.0_Setup.exe"
if (!(Test-Path -LiteralPath $SetupExe)) {
    throw "Inno Setup completed without producing PRM_Billing_Inventory_V1.0_Setup.exe"
}
if ((Get-Item -LiteralPath $SetupExe).LastWriteTime -lt $BuildStarted) {
    throw "Inno Setup left a stale PRM_Billing_Inventory_V1.0_Setup.exe"
}
if ($InternalPrereleaseHash) {
    if (!(Test-Path -LiteralPath $InternalPrereleaseSetup)) {
        throw "Official V1.0 build removed the preserved internal 1.7.8 setup"
    }
    $InternalPrereleaseHashAfter = (Get-FileHash -LiteralPath $InternalPrereleaseSetup -Algorithm SHA256).Hash
    if ($InternalPrereleaseHashAfter -ne $InternalPrereleaseHash) {
        throw "Official V1.0 build modified the preserved internal 1.7.8 setup"
    }
}
