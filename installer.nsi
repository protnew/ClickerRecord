; Скрипт инсталлятора для программы "Кликер"
!include "MUI2.nsh"

; Параметры приложения
!define APPNAME "Кликер"
!define COMPANYNAME "Кликер"
!define DESCRIPTION "Программа для записи и воспроизведения действий мыши и клавиатуры"
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 0
!define HELPURL "https://github.com/yourname/clicker" ; Здесь можно указать URL репозитория или сайта
!define UPDATEURL "https://github.com/yourname/clicker"
!define ABOUTURL "https://github.com/yourname/clicker"

; Общие настройки
Name "${APPNAME}"
OutFile "clicker_setup.exe"
InstallDir "$PROGRAMFILES\${APPNAME}"
InstallDirRegKey HKLM "Software\${APPNAME}" "Install_Dir"
RequestExecutionLevel admin

; Интерфейс
!define MUI_ICON "icon.ico"
!define MUI_UNICON "icon.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "installer_welcome.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "installer_welcome.bmp"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "installer_header.bmp"
!define MUI_ABORTWARNING

; Страницы инсталлятора
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "license.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
    
; Добавление опционального создания ярлыка на рабочем столе
!define MUI_FINISHPAGE_RUN "$INSTDIR\clicker.exe"
!define MUI_FINISHPAGE_SHOWREADME ""
!define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
!define MUI_FINISHPAGE_SHOWREADME_TEXT "Создать ярлык на рабочем столе"
!define MUI_FINISHPAGE_SHOWREADME_FUNCTION createDesktopShortcut
!insertmacro MUI_PAGE_FINISH

; Настройка деинсталлятора
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Языки
!insertmacro MUI_LANGUAGE "Russian"

; Установка
Section "Установить"
  SetOutPath "$INSTDIR"
  
  ; Копирование файлов
  File "dist\clicker.exe"
  File "icon.ico"
  File "README.md"
  
  ; Хранение информации об установке
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "QuietUninstallString" '"$INSTDIR\uninstall.exe" /S'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$INSTDIR\icon.ico"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${COMPANYNAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "HelpLink" "${HELPURL}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLUpdateInfo" "${UPDATEURL}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLInfoAbout" "${ABOUTURL}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMinor" ${VERSIONMINOR}
  
  ; Создание деинсталлятора
  WriteUninstaller "$INSTDIR\uninstall.exe"
  
  ; Создание ярлыков в меню Пуск
  CreateDirectory "$SMPROGRAMS\${APPNAME}"
  CreateShortcut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\clicker.exe" "" "$INSTDIR\icon.ico"
  CreateShortcut "$SMPROGRAMS\${APPNAME}\Удалить ${APPNAME}.lnk" "$INSTDIR\uninstall.exe"
SectionEnd

; Деинсталляция
Section "Uninstall"
  ; Удаление файлов и папок
  Delete "$INSTDIR\clicker.exe"
  Delete "$INSTDIR\icon.ico"
  Delete "$INSTDIR\README.md"
  Delete "$INSTDIR\uninstall.exe"
  
  ; Удаление ярлыков
  Delete "$DESKTOP\${APPNAME}.lnk"
  Delete "$SMPROGRAMS\${APPNAME}\*.*"
  RMDir "$SMPROGRAMS\${APPNAME}"
  RMDir "$INSTDIR"
  
  ; Удаление записей реестра
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
  DeleteRegKey HKLM "Software\${APPNAME}"
SectionEnd

; Функция для создания ярлыка на рабочем столе
Function createDesktopShortcut
  CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\clicker.exe" "" "$INSTDIR\icon.ico"
FunctionEnd 