@echo off
REM The MotorEase folder (where the .bat files are located). It is the "home" of everything.
set "BASE=C:\Projetos\MotorEase\ana_MotorEase\MotorEase"

REM a11y-argus repo (contains automate_accessibility.py and apks.csv).
set "ARGUS_DIR=C:\Users\dasil\PycharmProjects\ocr-test"

REM Python from the PROPRIO argus venv (has lxml, cv2, droidbot etc).
REM Step 1 uses this interpreter, not the MotorEase one.
REM Default = .venv inside ocr-test. Adjust if your venv has a different name or location.
set "ARGUS_PYTHON=%ARGUS_DIR%\.venv\Scripts\python.exe"

set "APKS_CSV=C:\Users\dasil\OneDrive\Documentos\a11y-argus-defaults\apks.csv"

REM ---- outputs and workbooks: all within MotorEase ----
set "ARGUS_DATA=%BASE%\argus_data"
set "MOTOREASE_INPUT=%BASE%\motorease_input"
set "REPORTS_DIR=%BASE%\me_reports"
set "COMPARACAO_OUT=%BASE%\comparacao.json"
set "MATCH_OUT=%BASE%\match.json"

REM ---- MotorEase ----
set "MOTOREASE_PY=%BASE%\Code\MotorEase.py"
set "MOTOREASE_PROJECT_DIR=%BASE%"

set "PREPARE_PY=%BASE%\prepare_motorease_input.py"
set "COMPARE_PY=%BASE%\compare_argus_motorease.py"
set "MATCH_PY=%BASE%\match_target_size.py"

REM ---- parameters ----
set "PYTHON=python"
set "VARIANT=default"
set "IOMIN=0.5"
