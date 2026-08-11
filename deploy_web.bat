@echo off
chcp 65001 >nul
echo ==========================================
echo BIST DASHBOARD - OTO DEPLOY VE VERSIYON GUNCELLEYICI
echo ==========================================
echo.

:: O anki tarihi ve saati alip dateStr degiskenine atiyoruz
FOR /F "tokens=*" %%i IN ('powershell -Command "Get-Date -Format 'dd.MM.yyyy-HH.mm'"') DO SET dateStr=%%i

echo 1. Versiyon numarasi guncelleniyor...
powershell -Command "(Get-Content 'frontend\lib\screens\home_screen.dart' -Encoding UTF8) -replace 'Versiyon \([^)]+\)', 'Versiyon (%%dateStr%%)' | Set-Content 'frontend\lib\screens\home_screen.dart' -Encoding UTF8"
echo Yeni Versiyon: %dateStr%

echo.
echo 2. Degisiklikler GitHub'a gonderiliyor (GitHub Pages + Render.com otomatik tetikleniyor)...
git add .
git commit -m "Versiyon Guncellemesi: %dateStr%"
git push origin main

echo.
echo ==========================================
echo DEPLOY ISLEMI BASARIYLA TETIKLENDI!
echo 1. GitHub Pages (Frontend) otomatik derlenip yayinlanacak.
echo 2. Render.com (Backend API) otomatik guncellenecek.
echo Canli Backend API: https://bistdashboard-9pag.onrender.com
echo ==========================================
pause
