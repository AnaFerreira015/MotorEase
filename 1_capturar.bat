@echo off

setlocal enabledelayedexpansion
cd /d "%~dp0"
call config.bat
if "%FORCE%"=="" set "FORCE=0"

echo ===================================================================
echo  STEP 1/4 - a11y-argus (droidbot + analysis)
echo ===================================================================
if not "%DROIDBOT_DIR%"=="" (
    set "PYTHONPATH=%DROIDBOT_DIR%;%PYTHONPATH%"
    echo   using a customized DroidBot: %DROIDBOT_DIR%
)
if not "%APKS_CSV%"=="" (
    if not exist "%APKS_CSV%" (
        echo ERROR: APKS_CSV not found in "%APKS_CSV%"
        exit /b 1
    )
    copy /Y "%APKS_CSV%" "%ARGUS_DIR%\apks.csv" >nul
    echo   using apks.csv: %APKS_CSV%
)
if not exist "%ARGUS_PYTHON%" (
    echo ERROR: could not find the Python for the Argus venv at:
    echo   "%ARGUS_PYTHON%"
    echo Adjust ARGUS_PYTHON in config.bat. To find the path, run:
    echo   dir "%ARGUS_DIR%\*python.exe" /s /b
    exit /b 1
)
pushd "%ARGUS_DIR%"
"%ARGUS_PYTHON%" automate_accessibility.py
if errorlevel 1 ( echo ERROR at the Argus stage & popd & exit /b 1 )
popd

echo.
echo ===================================================================
echo  STEP 2/4 - collecting Argus outputs (only apps from apks.csv)
echo ===================================================================
if not exist "%ARGUS_DATA%" mkdir "%ARGUS_DATA%"
for /f "usebackq delims=" %%L in ("%ARGUS_DIR%\apks.csv") do (
    if /I "%%~xL"==".apk" (
        if exist "%ARGUS_DIR%\output_dir_%%~nL" (
            echo   copying output_dir_%%~nL
            xcopy /E /I /Y "%ARGUS_DIR%\output_dir_%%~nL" "%ARGUS_DATA%\output_dir_%%~nL\" >nul
        ) else (
            echo   [notice] no Argus output for "%%~nL" ^(output_dir_%%~nL it doesn't exist^)
        )
    )
)

echo.
echo ===================================================================
echo  STEP 3/4 - assembling the MotorEase bridge
echo ===================================================================
"%PYTHON%" "%PREPARE_PY%" "%ARGUS_DATA%" "%MOTOREASE_INPUT%" --variant "%VARIANT%"
if errorlevel 1 ( echo Error during the prepare stage & exit /b 1 )

echo.
echo ===================================================================
echo  STEP 4/4 - MotorEase via app
echo ===================================================================
if not exist "%REPORTS_DIR%" mkdir "%REPORTS_DIR%"
for /d %%D in ("%MOTOREASE_INPUT%\*") do (
    set "app=%%~nxD"
    set "report=AccessibilityReport_!app!.json"

    set "skip=0"
    if "!FORCE!" NEQ "1" if exist "%REPORTS_DIR%\!report!" set "skip=1"

    if "!skip!"=="1" (
        echo   [skipping] !app! ^(Report already exists; use FORCE=1 to redo^)
    ) else (
        echo   [rodando] !app!
        "%PYTHON%" "%MOTOREASE_PY%" "%%~fD"
        if exist "%MOTOREASE_PROJECT_DIR%\!report!" (
            move /Y "%MOTOREASE_PROJECT_DIR%\!report!" "%REPORTS_DIR%\!report!" >nul
            echo     -^> %REPORTS_DIR%\!report!
        ) else (
            echo     WARNING: I couldn't find !report! in %MOTOREASE_PROJECT_DIR%
        )
    )
)

echo.
echo Capture completed. Reports in: %REPORTS_DIR%
echo Now run 2_comparar.bat and 3_match.bat
endlocal
