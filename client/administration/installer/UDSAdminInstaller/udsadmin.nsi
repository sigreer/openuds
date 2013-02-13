# Auto-generated by EclipseNSIS Script Wizard
# 28-nov-2011 9:41:00

Name "UDS Administration"

# General Symbol Definitions
!define REGKEY "SOFTWARE\$(^Name)"
!define VERSION 1.0
!define COMPANY "Virtual Cable S.L."
!define URL http://www.virtualcable.es

# MultiUser Symbol Definitions
!define MULTIUSER_EXECUTIONLEVEL Admin
!define MULTIUSER_INSTALLMODE_COMMANDLINE
!define MULTIUSER_INSTALLMODE_INSTDIR "UDS Administration Client"
!define MULTIUSER_INSTALLMODE_INSTDIR_REGISTRY_KEY "${REGKEY}"
!define MULTIUSER_INSTALLMODE_INSTDIR_REGISTRY_VALUE "Path"

# MUI Symbol Definitions
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\orange-install.ico"
!define MUI_FINISHPAGE_NOAUTOCLOSE
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\orange-uninstall.ico"
!define MUI_UNFINISHPAGE_NOAUTOCLOSE
!define MUI_LANGDLL_REGISTRY_ROOT HKLM
!define MUI_LANGDLL_REGISTRY_KEY ${REGKEY}
!define MUI_LANGDLL_REGISTRY_VALUENAME InstallerLanguage

# Included files
!include MultiUser.nsh
!include Sections.nsh
!include MUI2.nsh

# Reserved Files
!insertmacro MUI_RESERVEFILE_LANGDLL

# Variables
Var StartMenuGroup

# Installer pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE license.txt
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

# Installer languages
!insertmacro MUI_LANGUAGE English
!insertmacro MUI_LANGUAGE Spanish
!insertmacro MUI_LANGUAGE French
!insertmacro MUI_LANGUAGE German

# Installer attributes
OutFile UDSAdminSetup.exe
InstallDir "UDS Administration Client"
CRCCheck on
XPStyle on
ShowInstDetails show
VIProductVersion 1.0.0.0
VIAddVersionKey /LANG=${LANG_ENGLISH} ProductName "UDS Administration Client"
VIAddVersionKey /LANG=${LANG_ENGLISH} ProductVersion "${VERSION}"
VIAddVersionKey /LANG=${LANG_ENGLISH} CompanyName "${COMPANY}"
VIAddVersionKey /LANG=${LANG_ENGLISH} CompanyWebsite "${URL}"
VIAddVersionKey /LANG=${LANG_ENGLISH} FileVersion "${VERSION}"
VIAddVersionKey /LANG=${LANG_ENGLISH} FileDescription ""
VIAddVersionKey /LANG=${LANG_ENGLISH} LegalCopyright ""
InstallDirRegKey HKLM "${REGKEY}" Path
ShowUninstDetails show

# Installer sections
Section -Main SEC0000
    SetOutPath $INSTDIR
    SetOverwrite on
    File ..\..\UdsAdmin\bin\Release\CookComputing.XmlRpcV2.dll
    File ..\..\UdsAdmin\bin\Release\UdsAdmin.exe
    File ..\..\UdsAdmin\bin\Release\UdsAdmin.exe.config
    SetOutPath $SMPROGRAMS\$StartMenuGroup
    CreateShortcut "$SMPROGRAMS\$StartMenuGroup\UDS Administration Client.lnk" $INSTDIR\UdsAdmin.exe
    SetOutPath $INSTDIR\de
    File ..\..\UdsAdmin\bin\Release\de\UdsAdmin.resources.dll
    SetOutPath $INSTDIR\es
    File ..\..\UdsAdmin\bin\Release\es\UdsAdmin.resources.dll
    SetOutPath $INSTDIR\fr
    File ..\..\UdsAdmin\bin\Release\fr\UdsAdmin.resources.dll

    SetOutPath $TEMP
    File MSChart.exe
    System::Call "kernel32::CreateMutexA(i 0, i 0, t 'ChartInstall') i .r0 ?e"
    ExecWait "$TEMP\MSChart.exe /q /log %temp%\msclog.htm /norestart" $0
    Delete "$TEMP\MSChart.exe"

    WriteRegStr HKLM "${REGKEY}\Components" Main 1
SectionEnd

Section -post SEC0001
    WriteRegStr HKLM "${REGKEY}" Path $INSTDIR
    SetOutPath $INSTDIR
    WriteUninstaller $INSTDIR\UDSAdminRemover.exe
    SetOutPath $SMPROGRAMS\$StartMenuGroup
    CreateShortcut "$SMPROGRAMS\$StartMenuGroup\$(^UninstallLink).lnk" $INSTDIR\UDSAdminRemover.exe
    WriteRegStr HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\$(^Name)" DisplayName "$(^Name)"
    WriteRegStr HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\$(^Name)" DisplayVersion "${VERSION}"
    WriteRegStr HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\$(^Name)" Publisher "${COMPANY}"
    WriteRegStr HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\$(^Name)" URLInfoAbout "${URL}"
    WriteRegStr HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\$(^Name)" DisplayIcon $INSTDIR\UDSAdminRemover.exe
    WriteRegStr HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\$(^Name)" UninstallString $INSTDIR\UDSAdminRemover.exe
    WriteRegDWORD HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\$(^Name)" NoModify 1
    WriteRegDWORD HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\$(^Name)" NoRepair 1
SectionEnd

# Macro for selecting uninstaller sections
!macro SELECT_UNSECTION SECTION_NAME UNSECTION_ID
    Push $R0
    ReadRegStr $R0 HKLM "${REGKEY}\Components" "${SECTION_NAME}"
    StrCmp $R0 1 0 next${UNSECTION_ID}
    !insertmacro SelectSection "${UNSECTION_ID}"
    GoTo done${UNSECTION_ID}
next${UNSECTION_ID}:
    !insertmacro UnselectSection "${UNSECTION_ID}"
done${UNSECTION_ID}:
    Pop $R0
!macroend

# Uninstaller sections
Section /o -un.Main UNSEC0000
    Delete /REBOOTOK $INSTDIR\fr\UdsAdmin.resources.dll
    Delete /REBOOTOK $INSTDIR\es\UdsAdmin.resources.dll
    Delete /REBOOTOK $INSTDIR\de\UdsAdmin.resources.dll
    Delete /REBOOTOK "$SMPROGRAMS\$StartMenuGroup\UDS Administration Client.lnk"
    Delete /REBOOTOK $INSTDIR\UdsAdmin.exe.config
    Delete /REBOOTOK $INSTDIR\UdsAdmin.exe
    Delete /REBOOTOK $INSTDIR\CookComputing.XmlRpcV2.dll
    DeleteRegValue HKLM "${REGKEY}\Components" Main
SectionEnd

Section -un.post UNSEC0001
    DeleteRegKey HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\$(^Name)"
    Delete /REBOOTOK "$SMPROGRAMS\$StartMenuGroup\$(^UninstallLink).lnk"
    Delete /REBOOTOK $INSTDIR\UDSAdminRemover.exe
    DeleteRegValue HKLM "${REGKEY}" Path
    DeleteRegKey /IfEmpty HKLM "${REGKEY}\Components"
    DeleteRegKey /IfEmpty HKLM "${REGKEY}"
    RmDir /REBOOTOK $SMPROGRAMS\$StartMenuGroup
    RmDir /REBOOTOK $INSTDIR
SectionEnd

# Installer functions
Function .onInit
    InitPluginsDir
    StrCpy $StartMenuGroup "Virtual Cable\UDS Administration Client"

    ReadRegDWORD $0 HKLM "SOFTWARE\Microsoft\NET Framework Setup\NDP\v3.5" SP
    ${if} $0 != 1
        MessageBox MB_OK "$(^NoDotNet)"
        Abort
    ${EndIf}


    !insertmacro MUI_LANGDLL_DISPLAY
    !insertmacro MULTIUSER_INIT
FunctionEnd

# Uninstaller functions
Function un.onInit
    StrCpy $StartMenuGroup "Virtual Cable\UDS Administration Client"
    !insertmacro MUI_UNGETLANGUAGE
    !insertmacro MULTIUSER_UNINIT
    !insertmacro SELECT_UNSECTION Main ${UNSEC0000}
FunctionEnd

# Installer Language Strings

LangString ^NoDotNet ${LANG_ENGLISH} ".NET 3.5 sp1 Required.$\nPlease, install it to proceed"
LangString ^NoDotNet ${LANG_SPANISH} "Se requiere .NET 3.5 sp1.$\nPor favor, instalelo para proceder"
LangString ^NoDotNet ${LANG_FRENCH} ".NET Framework 3.5 SP1 requis.$\nVeuillez, installez-le de procéder"
LangString ^NoDotNet ${LANG_GERMAN} "Erforderlich ist. NET 3.5 sp1.$\nPor Bitte installieren Sie es, um fortzufahren"


LangString ^UninstallLink ${LANG_ENGLISH} "Uninstall $(^Name)"
LangString ^UninstallLink ${LANG_SPANISH} "Desinstalar $(^Name)"
LangString ^UninstallLink ${LANG_FRENCH} "Désinstaller $(^Name)"
LangString ^UninstallLink ${LANG_GERMAN} "Deinstallieren $(^Name)"
