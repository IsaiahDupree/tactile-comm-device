@echo off
echo ===============================================
echo TACTILE COMMUNICATOR - COMPILATION TEST
echo ===============================================
echo.
echo This script helps verify the project setup.
echo.
echo Project Structure:
echo - tactile_communicator_local_libs.ino (main sketch)
echo - libraries/ (local libraries folder)
echo   - Adafruit_VS1053_Library/
echo   - PCF8575/
echo - config/ (SD card configuration files)
echo.
echo To test compilation:
echo 1. Open Arduino IDE
echo 2. Open tactile_communicator_local_libs.ino
echo 3. Arduino IDE will automatically detect local libraries
echo 4. Select your board (Arduino Uno/Nano/etc.)
echo 5. Click Verify/Compile
echo.
echo If compilation fails:
echo - Check that all libraries are in libraries/ folder
echo - Verify board selection matches your hardware
echo - Check serial monitor for detailed error messages
echo.
echo Libraries included:
dir /b libraries
echo.
echo Configuration files:
dir /b config
echo.
echo Press any key to exit...
pause >nul
