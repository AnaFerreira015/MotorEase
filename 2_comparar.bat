@echo off
setlocal
cd /d "%~dp0"
call config.bat

echo Comparing Argus vs. MotorEase -^> %COMPARACAO_OUT%
"%PYTHON%" "%COMPARE_PY%" "%ARGUS_DATA%" "%MOTOREASE_INPUT%" "%REPORTS_DIR%" "%COMPARACAO_OUT%"
if errorlevel 1 ( echo Comparison error & exit /b 1 )
echo Ready: %COMPARACAO_OUT%
endlocal
