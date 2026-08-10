@echo off
chcp 65001 >nul
echo ==========================================
echo OTO GUNCELLEME VE VERSIYON DEGISTIRICI
echo ==========================================
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
