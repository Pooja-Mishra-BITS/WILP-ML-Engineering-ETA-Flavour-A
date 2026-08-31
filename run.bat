@echo off
setlocal

set "DIR=%~dp0"
set "IMAGE=ml-engineering-mini-project"
set "APP=ml-engineering-mini-project"
set "MLFLOW=mlflow"

cd /d "%DIR%"

echo Creating MLflow folder...
if not exist "mlruns" mkdir "mlruns"

echo Building Docker image...
docker build -t "%IMAGE%" .
if errorlevel 1 goto failed

echo Starting MLflow...
docker ps -a --format "{{.Names}}" | findstr /x "%MLFLOW%" >nul

if not errorlevel 1 (
    docker start "%MLFLOW%" >nul 2>&1
) else (
    docker run -d --name "%MLFLOW%" --restart unless-stopped -p 5000:5000 -v "%DIR%mlruns:/mlruns" "%IMAGE%" mlflow ui --backend-store-uri /mlruns --host 0.0.0.0 --port 5000
)

echo Training model...
docker run --rm -v "%DIR%:/app" -w /app "%IMAGE%" python -m pipeline.train
if errorlevel 1 goto failed

echo Running monitoring...
docker run --rm -v "%DIR%:/app" -w /app "%IMAGE%" python -m pipeline.monitor
if errorlevel 1 goto failed

echo Running tests...
docker run --rm -v "%DIR%:/app" -w /app "%IMAGE%" python -m unittest discover -v
if errorlevel 1 goto failed

echo Rebuilding image with trained model...
docker build -t "%IMAGE%" .
if errorlevel 1 goto failed

echo Starting API...
docker rm -f "%APP%" >nul 2>&1
if not exist "logs" mkdir "logs"
docker run -d --name "%APP%" --restart unless-stopped -p 8000:8000 -v "%DIR%logs:/app/logs" "%IMAGE%"

echo.
echo Completed successfully.
echo API: http://127.0.0.1:8000
echo Swagger: http://127.0.0.1:8000/docs
echo MLflow: http://127.0.0.1:5000
pause
exit /b 0

:failed
echo.
echo A command failed. Check the message above.
pause
exit /b 1
