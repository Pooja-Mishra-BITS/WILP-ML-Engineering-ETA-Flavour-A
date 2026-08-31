@echo off
setlocal

set "DIR=%~dp0"
set "APP=ml-engineering-mini-project"
set "COUNT=%1"
if "%COUNT%"=="" set "COUNT=150"

cd /d "%DIR%"

echo Checking API container...
docker ps --format "{{.Names}}" | findstr /c:"%APP%" >nul
if errorlevel 1 (
    echo API container "%APP%" is not running. Run run.bat first.
    goto failed
)

echo Checking API health...
curl -s -f http://127.0.0.1:8000/health >nul
if errorlevel 1 (
    echo API is not responding on http://127.0.0.1:8000/health
    goto failed
)

echo Sending %COUNT% simulated real-time requests...
python -m client.live_client --count %COUNT% --interval 0.05
if errorlevel 1 goto failed

echo Submitting simulated feedback (actual outcomes) for accuracy drift...
python -m client.feedback_client
if errorlevel 1 goto failed

echo Computing accuracy drift report (predicted vs. actual)...
python -m pipeline.accuracy_report
if errorlevel 1 goto failed

echo Computing drift report...
python -m pipeline.drift_report
if errorlevel 1 goto failed

echo Building monitoring dashboard...
python -m pipeline.build_dashboard
if errorlevel 1 goto failed

echo Building observability dashboard...
python -m pipeline.build_observability_dashboard
if errorlevel 1 goto failed

echo.
echo Completed successfully.
echo Request/response log: %DIR%logs\client_requests.txt
echo Drift table: %DIR%reports\drift_table.md
echo Accuracy drift (predicted vs actual): %DIR%reports\accuracy_drift.md
start "" "%DIR%reports\dashboard.html"
start "" "%DIR%reports\observability_dashboard.html"
pause
exit /b 0

:failed
echo.
echo A command failed. Check the message above.
pause
exit /b 1
