@echo off
echo Eski backend islemleri temizleniyor...
for /f "tokens=5" %%a in ('netstat -aon ^| find "LISTENING" ^| find ":8001"') do taskkill /f /pid %%a 2>nul
echo Backend sunucusu baslatiliyor...
start "Backend API" cmd /c "cd backend && venv2\Scripts\python.exe -m uvicorn main:app --reload --port 8001"

echo.
echo Flutter web baslatiliyor...
cd frontend
flutter run -d edge --web-port 8080
pause
