@echo off
chcp 65001 >nul
echo ==========================================
echo   ChessDB - 国际象棋数据管理系统 启动脚本
echo ==========================================
echo.

set "SCRIPT_DIR=%~dp0"

REM 优先使用项目内的 .venv（如果存在），否则用系统中已激活的 Python
set "VENV_ACTIVATE=%SCRIPT_DIR%.venv\Scripts\activate.bat"
set "USE_VENV="
if exist "%VENV_ACTIVATE%" (
    set "USE_VENV=1"
)

REM ====== 启动后端 ======
echo [1/2] 启动后端服务（Flask :5000）...
if defined USE_VENV (
    start "ChessDB Backend" cmd /k "cd /d "%SCRIPT_DIR%backend" && call "%VENV_ACTIVATE%" && set FLASK_APP=run && set FLASK_ENV=development && flask run --port 5000 --host 0.0.0.0"
) else (
    start "ChessDB Backend" cmd /k "cd /d "%SCRIPT_DIR%backend" && set FLASK_APP=run && set FLASK_ENV=development && python -m flask run --port 5000 --host 0.0.0.0"
)

timeout /t 3 /nobreak >nul

REM ====== 启动前端 ======
echo [2/2] 启动前端服务（Vite :3000）...
start "ChessDB Frontend" cmd /k "cd /d "%SCRIPT_DIR%frontend" && npm run dev"

echo.
echo ==========================================
echo   Backend : http://localhost:5000
echo   Frontend: http://localhost:3000
echo   API Docs: http://localhost:5000/apidocs/
echo ==========================================
echo.
echo You can close this window. Servers run in separate windows.
pause
