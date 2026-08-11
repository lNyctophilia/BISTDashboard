@echo off
chcp 65001 >nul
echo ==========================================
echo BIST DASHBOARD - HIZLI OTO DEPLOY
echo ==========================================
echo.

:: 1. Tarih/Saat ve Git Remote URL bilgisini al
FOR /F "tokens=*" %%i IN ('powershell -Command "Get-Date -Format 'dd.MM.yyyy-HH.mm'"') DO SET dateStr=%%i
FOR /F "tokens=*" %%i IN ('git remote get-url origin') DO SET remoteUrl=%%i

echo 1. Versiyon numarasi guncelleniyor...
powershell -Command "(Get-Content 'frontend\lib\screens\home_screen.dart' -Encoding UTF8) -replace 'Versiyon \([^)]+\)', 'Versiyon (%%dateStr%%)' | Set-Content 'frontend\lib\screens\home_screen.dart' -Encoding UTF8"
echo Yeni Versiyon: %dateStr%
echo.

echo 2. Flutter Web yerelde derleniyor...
cd frontend
call flutter build web --release --base-href "/BISTDashboard/" --dart-define=API_URL="https://bistdashboard-9pag.onrender.com/api"

if not exist "build\web\auth-config.js" (
    echo auth-config.js kopyalaniyor...
    copy "web\auth-config.example.js" "build\web\auth-config.js" >nul
)

echo.
echo 3. Derlenen site GitHub Pages'a (gh-pages) aninda yukleniyor...
cd build\web
git init >nul
git add -A >nul
git commit -m "Web Deploy: %dateStr%" >nul
git branch -M gh-pages >nul
git remote add origin %remoteUrl% >nul
git push -f origin gh-pages
cd /d "%~dp0"
if exist "frontend\build\web\.git" rmdir /s /q "frontend\build\web\.git"

echo.
echo 4. Kaynak kodlar GitHub main branch'ine gonderiliyor...
git add .
git commit -m "Versiyon Guncellemesi: %dateStr%"
git push origin main

echo.
echo ==========================================
echo DEPLOY ISLEMI BASARIYLA TAMAMLANDI!
echo 1. GitHub Pages (Frontend) ~15 saniye icinde canliya gececek.
echo 2. Render.com (Backend API) main push ile otomatik guncellenecek.
echo Canli Site: https://lnyctophilia.github.io/BISTDashboard/
echo Canli Backend API: https://bistdashboard-9pag.onrender.com
echo ==========================================
pause
