@echo off
cd /d "%~dp0"
if exist "dist\desktop-pet-0.10.0-rc.3\CodexGarden.exe" (
 start "" "dist\desktop-pet-0.10.0-rc.3\CodexGarden.exe"
) else (
 call npm start
)
