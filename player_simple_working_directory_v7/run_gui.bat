@echo off
echo Installing dependencies for Tactile Data Tool GUI...

REM Install required packages
pip install pyserial pillow

echo.
echo Starting Tactile Data Tool GUI...
python data_gui_tk.py
pause
