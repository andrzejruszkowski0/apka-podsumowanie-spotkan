@echo off
setlocal

set "ROOT=%~dp0"

echo Uruchamiam backend i frontend...

start "Backend - Analiza spotkan" cmd /k "cd /d "%ROOT%backend" && call .venv\Scripts\activate.bat && uvicorn app.main:app --host 127.0.0.1 --port 8000"

start "Frontend - Analiza spotkan" cmd /k "cd /d "%ROOT%frontend" && npm run dev"

timeout /t 5 /nobreak >nul
start "" "http://localhost:5173"

endlocal
