@echo off
setlocal

set "DIR=%~dp0"
cd /d "%DIR%"

echo Cleaning MLflow tracking data and generated project artifacts only...

REM Remove only the MLflow container, not the application container
for %%c in (mlflow) do (
    docker rm -f %%c >nul 2>&1
)

REM Remove MLflow tracking store
if exist "mlruns" (
    echo Removing mlruns...
    rmdir /s /q "mlruns"
)

REM Remove generated logs and outputs produced by the pipeline
for %%d in (logs experiments reports artifacts) do (
    if exist "%%d" (
        echo Removing %%d...
        rmdir /s /q "%%d"
    )
)

REM Recreate empty folders so the app can regenerate them cleanly
for %%d in (mlruns logs experiments reports artifacts) do (
    if not exist "%%d" mkdir "%%d"
)

echo.
echo MLflow and artifacts cleaned successfully.
echo You can now run: run.bat
pause
exit /b 0
