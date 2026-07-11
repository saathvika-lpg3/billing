#define MyAppName "PRM Billing Inventory"
#define MyAppVersion "1.7.4"
#define MyAppPublisher "PRM Software Solutions"
#define MyAppExeName "PRM_Billing_Inventory.exe"

[Setup]
AppId={{7E5E6B90-836B-4D97-B252-7C08A6BE1001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\PRM Billing Inventory
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\installer_output
OutputBaseFilename=PRM_Billing_Inventory_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
LicenseFile=PRM_Billing_Inventory_Electronic_Agreement.txt
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Preserve an existing client database during upgrades. The separately copied
; database is a sanitized, unbound first-install seed produced by the build.
Source: "..\dist\PRM_Billing_Inventory\*"; DestDir: "{app}"; Excludes: "_internal\database\prm_billing_inventory.db"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\dist\PRM_Billing_Inventory\_internal\database\prm_billing_inventory.db"; DestDir: "{app}\_internal\database"; Flags: ignoreversion onlyifdoesntexist uninsneveruninstall

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
var
  LicensePage: TInputFileWizardPage;
  ClientLicenseFile: string;

function IsValidClientLicenseFile(FileName: string; var ErrorText: string): Boolean;
var
  RawText: AnsiString;
  Ext: string;
begin
  Result := False;
  ErrorText := '';

  if Trim(FileName) = '' then
  begin
    ErrorText := 'Client .prmlic file is required. Installation cannot continue.';
    Exit;
  end;

  if not FileExists(FileName) then
  begin
    ErrorText := 'Selected .prmlic file was not found.';
    Exit;
  end;

  Ext := Lowercase(ExtractFileExt(FileName));
  if Ext <> '.prmlic' then
  begin
    ErrorText := 'Select the .prmlic file exported from PRM Client Management.';
    Exit;
  end;

  if not LoadStringFromFile(FileName, RawText) then
  begin
    ErrorText := 'Selected .prmlic file could not be read.';
    Exit;
  end;

  if Pos('PRMLIC1.', RawText) = 1 then
  begin
    Result := True;
    Exit;
  end;

  if (Pos('"client_company_name"', RawText) > 0) and
     (Pos('"phone_number"', RawText) > 0) and
     (Pos('"area"', RawText) > 0) and
     (Pos('"license_key"', RawText) > 0) and
     (Pos('"installation_key"', RawText) > 0) and
     (Pos('"super_admin_username"', RawText) > 0) and
     (Pos('"super_admin_password"', RawText) > 0) and
     (Pos('"developer_login_key"', RawText) > 0) and
     (Pos('"plan"', RawText) > 0) and
     (Pos('"expiry_date"', RawText) > 0) and
     (Pos('"status"', RawText) > 0) and
     (Pos('"business_type_code"', RawText) > 0) then
  begin
    Result := True;
    Exit;
  end;

  ErrorText := 'Selected file is not a valid PRM client license export.';
end;

function InitializeSetup(): Boolean;
var
  ErrorText: string;
begin
  Result := True;
  ClientLicenseFile := ExpandConstant('{param:ClientLicenseFile|}');
  if WizardSilent then
  begin
    if not IsValidClientLicenseFile(ClientLicenseFile, ErrorText) then
    begin
      MsgBox(ErrorText, mbCriticalError, MB_OK);
      Result := False;
      Exit;
    end;
  end;
end;

procedure InitializeWizard();
begin
  LicensePage := CreateInputFilePage(
    wpSelectDir,
    'Client License',
    'Select the client .prmlic file',
    'Installation will continue only with the PRM client license exported from Client Management.'
  );
  LicensePage.Add('Browse and select client .prmlic file:', 'PRM license files (*.prmlic)|*.prmlic|All files (*.*)|*.*', '.prmlic');
  if ClientLicenseFile <> '' then
    LicensePage.Values[0] := ClientLicenseFile;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  ErrorText: string;
begin
  Result := True;
  if CurPageID = LicensePage.ID then
  begin
    ClientLicenseFile := LicensePage.Values[0];
    if not IsValidClientLicenseFile(ClientLicenseFile, ErrorText) then
    begin
      MsgBox(ErrorText, mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ErrorText: string;
  DestDir: string;
  DestFile: string;
begin
  if CurStep = ssPostInstall then
  begin
    if ClientLicenseFile = '' then
      ClientLicenseFile := LicensePage.Values[0];
    if not IsValidClientLicenseFile(ClientLicenseFile, ErrorText) then
      RaiseException(ErrorText);

    DestDir := ExpandConstant('{app}\license');
    ForceDirectories(DestDir);
    DestFile := DestDir + '\client.prmlic';
    if not CopyFile(ClientLicenseFile, DestFile, False) then
      RaiseException('Could not install client license file.');
  end;
end;
