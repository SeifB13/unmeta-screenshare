; Inno Setup 6 script: iscc /DAppVersion=0.1.0 packaging\windows\installer.iss
; Packs dist\unmeta (PyInstaller output) into dist\UnMeta-Screenshare-Setup-<version>.exe.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{6F4B2D1E-8C3A-4E5F-9B7D-2A1C0E9F3B64}
AppName=UnMeta Screenshare
AppVersion={#AppVersion}
AppPublisher=UnMeta Screenshare contributors
AppPublisherURL=https://github.com/SeifB13/unmeta-screenshare
DefaultDirName={autopf}\UnMeta Screenshare
DefaultGroupName=UnMeta Screenshare
DisableProgramGroupPage=yes
; Per-user install by default: no admin rights needed.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
LicenseFile=..\..\LICENSE
OutputDir=..\..\dist
OutputBaseFilename=UnMeta-Screenshare-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName=UnMeta Screenshare
UninstallDisplayIcon={app}\unmeta.exe
SetupIconFile=unmeta.ico

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "fr"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\dist\unmeta\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\UnMeta Screenshare"; Filename: "{app}\unmeta.exe"; WorkingDir: "{app}"
Name: "{group}\{cm:UninstallProgram,UnMeta Screenshare}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\UnMeta Screenshare"; Filename: "{app}\unmeta.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\unmeta.exe"; Description: "{cm:LaunchProgram,UnMeta Screenshare}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Stop the adb server shipped with the app so its files can be removed.
Filename: "{app}\_internal\vendor\scrcpy\adb.exe"; Parameters: "kill-server"; Flags: runhidden skipifdoesntexist; RunOnceId: "KillAdb"
