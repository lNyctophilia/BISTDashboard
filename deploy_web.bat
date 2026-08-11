@echo off
chcp 65001 >nul
echo ==========================================
echo OTO DEPLOY VE VERSIYON DEGISTIRICI
echo ==========================================
echo.

echo 1. Eski backend islemleri temizleniyor ve backend sunucusu baslatiliyor...
for /f "tokens=5" %%a in ('netstat -aon ^| find "LISTENING" ^| find ":8001"') do taskkill /f /pid %%a 2>nul
start "Backend API" cmd /c "cd backend && venv2\Scripts\python.exe -m uvicorn main:app --reload --port 8001"
echo.

:: O anki tarihi ve saati alip dateStr degiskenine atiyoruz
FOR /F "tokens=*" %%i IN ('powershell -Command "Get-Date -Format 'dd.MM.yyyy-HH.mm'"') DO SET dateStr=%%i

echo 2. Versiyon numarasi guncelleniyor...
powershell -Command "(Get-Content 'frontend\lib\screens\home_screen.dart' -Encoding UTF8) -replace 'Versiyon \([^)]+\)', 'Versiyon (%dateStr%)' | Set-Content 'frontend\lib\screens\home_screen.dart' -Encoding UTF8"
echo Yeni Versiyon: %dateStr%

echo.
echo 3. Git ile degisiklikler Github'a gonderiliyor (GitHub Actions otomasyonu tetikleniyor)...
git add .
git commit -m "Versiyon Guncellemesi: %dateStr%"
git push origin main

echo.
echo ==========================================
echo DEPLOY ISLEMI BASARIYLA TETIKLENDI!
echo GitHub Pages Action otomatik derleme ve yayinlama surecini baslatti.
echo ==========================================
pause
