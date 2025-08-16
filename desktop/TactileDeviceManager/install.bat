@echo off
echo Installing Tactile Device Manager...
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo Node.js found: 
node --version

REM Install dependencies
echo.
echo Installing dependencies...
npm install

if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Installation complete!
echo.
echo To run the application:
echo   npm start
echo.
echo To build for distribution:
echo   npm run build-win
echo.
pause
