
@echo off
title Meta Quest 3 - Diffusion VR

echo ==================================
echo    META QUEST 3 - DIFFUSION VR
echo ==================================
echo.

echo [1/3] Connexion au Quest 3...

adb connect 192.168.1.80:5555

echo.
echo [2/3] Verification de la connexion...

adb -s 192.168.1.80:5555 get-state 2>nul | findstr /x "device" >nul

if errorlevel 1 (
    echo.
    echo ERREUR : Quest 3 inaccessible.
    echo Verifie que le casque est allume
    echo et connecte au Wi-Fi.
    echo.
    echo Si necessaire, reactive ADB via USB.
    pause
    exit /b 1
)

echo Quest 3 connecte !
echo.
echo [3/3] Lancement de la diffusion...

scrcpy -s 192.168.1.80:5555 --no-control --max-fps=60 --crop=1900:1400:100:300 --angle=20 --video-bit-rate=12M --audio-dup --fullscreen

echo.
echo Diffusion terminee.
pause
