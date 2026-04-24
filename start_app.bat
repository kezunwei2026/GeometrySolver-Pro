@echo off
chcp 65001 > nul
set ROOT=%~dp0

echo ======================================================
echo   AI Geometry Solver - Start Script
echo ======================================================

if not exist "%ROOT%admin" mkdir "%ROOT%admin"

echo [1/2] Starting backend (FastAPI)...
start "AI-Geo-Backend" cmd /k "cd /d "%ROOT%app\backend" && python main.py"

timeout /t 2 /nobreak > nul

echo [2/2] Starting frontend (Vite)...
start "AI-Geo-Frontend" cmd /k "cd /d "%ROOT%app\frontend" && npm run dev"

echo.
echo Backend:  http://0.0.0.0:8001
echo Frontend: http://0.0.0.0:5173
echo LAN access: use this computer's IP, e.g. http://YOUR_IP:5173
echo Admin dir reserved at: %ROOT%admin
echo ======================================================
pause
