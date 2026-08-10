@echo off
echo Backend sunucusu baslatiliyor (Simge durumunda)...
start /MIN "Backend API" cmd /c "cd backend && venv2\Scripts\python.exe -m uvicorn main:app --reload --port 8000"

echo.
echo Flutter web baslatiliyor...
cd frontend
flutter run -d edge --web-port 8080
pause
