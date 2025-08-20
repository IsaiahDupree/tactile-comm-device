@echo off
echo Installing dependencies...
python -m pip install pyserial

echo.
echo Launching Tactile Data Tool GUI (Tkinter version)...
python data_gui_tk.py

pause
