@echo off
REM ============================================================================
REM rodar_motorease.bat - roda SO o MotorEase, sem mexer no argus.
REM
REM Uso:
REM   rodar_motorease.bat                              (todos os apps; pula os que ja tem relatorio)
REM   set FORCE=1 && rodar_motorease.bat               (refaz TODOS)
REM   rodar_motorease.bat "Drive_Weather_With_Live_Radar_APKPure"   (refaz so esse app)
REM
REM O nome do app e o nome da pasta dentro de motorease_input.
REM ============================================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"
call config.bat
if "%FORCE%"=="" set "FORCE=0"
if not exist "%REPORTS_DIR%" mkdir "%REPORTS_DIR%"

set "ONLY=%~1"

if not "%ONLY%"=="" (
    REM ---- rodar so um app, sempre refazendo ----
    set "appdir=%MOTOREASE_INPUT%\%ONLY%"
    if not exist "!appdir!" (
        echo ERRO: pasta de entrada nao existe: "!appdir!"
        echo Confira o nome exato dentro de %MOTOREASE_INPUT%
        exit /b 1
    )
    set "report=AccessibilityReport_%ONLY%.json"
    echo [rodando] %ONLY%
    "%PYTHON%" "%MOTOREASE_PY%" "!appdir!"
    if exist "%MOTOREASE_PROJECT_DIR%\!report!" (
        move /Y "%MOTOREASE_PROJECT_DIR%\!report!" "%REPORTS_DIR%\!report!" >nul
        echo   -^> %REPORTS_DIR%\!report!
    ) else (
        echo   AVISO: nao encontrei !report! em %MOTOREASE_PROJECT_DIR%
    )
    echo Pronto. Agora rode 2_comparar.bat e 3_match.bat
    endlocal
    exit /b 0
)

REM ---- rodar todos ----
for /d %%D in ("%MOTOREASE_INPUT%\*") do (
    set "app=%%~nxD"
    set "report=AccessibilityReport_!app!.json"

    set "skip=0"
    if "!FORCE!" NEQ "1" if exist "%REPORTS_DIR%\!report!" set "skip=1"

    if "!skip!"=="1" (
        echo   [pulando] !app! ^(relatorio ja existe; use FORCE=1 para refazer^)
    ) else (
        echo   [rodando] !app!
        "%PYTHON%" "%MOTOREASE_PY%" "%%~fD"
        if exist "%MOTOREASE_PROJECT_DIR%\!report!" (
            move /Y "%MOTOREASE_PROJECT_DIR%\!report!" "%REPORTS_DIR%\!report!" >nul
            echo     -^> %REPORTS_DIR%\!report!
        ) else (
            echo     AVISO: nao encontrei !report! em %MOTOREASE_PROJECT_DIR%
        )
    )
)
echo Pronto. Agora rode 2_comparar.bat e 3_match.bat
endlocal
