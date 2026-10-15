@echo off
cd /d "%~dp0"
if exist "dist\desktop-pet-rc010\CodexGarden.exe" (
 start "" "dist\desktop-pet-rc010\CodexGarden.exe"
) else (
 call npm start
)
