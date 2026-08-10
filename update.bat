@echo off
chcp 65001 >nul
echo ==========================================
echo OTO GUNCELLEME VE VERSIYON DEGISTIRICI
echo ==========================================
echo.
echo 1. Versiyon numarasi guncelleniyor...
powershell -Command "$dateStr = Get-Date -Format 'dd.MM.yyyy-HH.mm'; $file = 'frontend\lib\screens\home_screen.dart'; (Get-Content $file -Encoding UTF8) -replace 'Versiyon \([^)]+\)', \"Versiyon ($dateStr)\" | Set-Content $file -Encoding UTF8; Write-Host \"Yeni Versiyon: $dateStr\""

echo.
echo 2. Flutter Web Build aliniyor...
cd frontend
call flutter build web
cd ..

echo.
echo 3. Git ile degisiklikler sunucuya gonderiliyor...
git add .
git commit -m "Otomatik Guncelleme"
git push

echo.
echo ==========================================
echo GUNCELLEME TAMAMLANDI!
echo ==========================================
pause
