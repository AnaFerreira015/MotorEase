@echo off
setlocal
cd /d "%~dp0"
call config.bat

set "iomin=%~1"
if "%iomin%"=="" set "iomin=%IOMIN%"
if "%iomin%"=="" set "iomin=0.5"

echo Match de target size (IoMin=%iomin%) -^> %MATCH_OUT%
"%PYTHON%" "%MATCH_PY%" "%ARGUS_DATA%" "%MOTOREASE_INPUT%" "%REPORTS_DIR%" "%MATCH_OUT%" --iomin "%iomin%"
if errorlevel 1 ( echo ERROR no match & exit /b 1 )
echo Ready: %MATCH_OUT%
endlocal
