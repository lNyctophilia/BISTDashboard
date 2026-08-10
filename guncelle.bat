@echo off
chcp 65001 >nul
echo ==========================================
echo OTO GUNCELLEME VE VERSIYON DEGISTIRICI
echo ==========================================
echo.

echo 0. Eski backend islemleri temizleniyor...
for /f "tokens=5" %%a in ('netstat -aon ^| find "LISTENING" ^| find ":8000"') do taskkill /f /pid %%a 2>nul
echo Backend sunucusu baslatiliyor...
start "Backend API" cmd /c "cd backend && venv2\Scripts\python.exe -m uvicorn main:app --reload --port 8000"
echo.

:: O anki tarihi ve saati alip dateStr degiskenine atiyoruz
FOR /F "tokens=*" %%i IN ('powershell -Command "Get-Date -Format 'dd.MM.yyyy-HH.mm'"') DO SET dateStr=%%i

echo 1. Versiyon numarasi guncelleniyor...
powershell -Command "$file = 'frontend\lib\screens\home_screen.dart'; (Get-Content $file -Encoding UTF8) -replace 'Versiyon \([^)]+\)', \"Versiyon (%dateStr%)\" | Set-Content $file -Encoding UTF8"
echo Yeni Versiyon: %dateStr%

echo.
echo 2. Flutter Web Build aliniyor...
cd frontend
call flutter build web
cd ..

echo.
echo 3. Git ile degisiklikler Github'a gonderiliyor...
git add .
git commit -m "Versiyon Guncellemesi: %dateStr%"
git push

echo.
echo ==========================================
echo GUNCELLEME TAMAMLANDI!
echo ==========================================
pause
