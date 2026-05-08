@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

if not exist "backend\manage.py" (
  echo [start-dev] 未找到 backend\manage.py，请确认在项目根目录运行。
  pause
  exit /b 1
)
if not exist "frontend\package.json" (
  echo [start-dev] 未找到 frontend\package.json。
  pause
  exit /b 1
)

echo.
echo HOTA-MDS 一键启动
echo   后端 Django: http://127.0.0.1:8000  ^(与 backend/Dockerfile 一致^)
echo   前端 Vite:   http://127.0.0.1:5173  ^(默认端口；/api 见 frontend/vite.config.js 代理到后端^)
echo.

if not exist "frontend\node_modules\" (
  echo [提示] 未检测到 frontend\node_modules，请先执行: cd frontend ^&^& npm install
  echo.
)

REM 新开窗口：后端（优先使用 backend\.venv）
start "HOTA-MDS Backend" cmd /k cd /d "%~dp0backend" ^&^& if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat ^&^& python manage.py runserver 0.0.0.0:8000

timeout /t 1 /nobreak >nul

REM 新开窗口：前端
start "HOTA-MDS Frontend" cmd /k cd /d "%~dp0frontend" ^&^& npm run dev

echo 已打开两个命令行窗口；关闭对应窗口即停止该服务。
echo.
pause
