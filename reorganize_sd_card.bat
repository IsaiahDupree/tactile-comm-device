@echo off
echo ===============================================================================
echo SD CARD REORGANIZATION SCRIPT - TWO-BANK PRIORITY MODE
echo ===============================================================================
echo.
echo This script will reorganize your SD card to support proper priority mode
echo functionality by moving personal recordings to the beginning of each folder.
echo.
echo BACKUP YOUR SD CARD FIRST!
echo.
pause

echo.
echo Step 1: Creating backup...
if not exist "C:\Users\Isaia\Documents\3D Printing\Projects\Button\SD_BACKUP" (
    mkdir "C:\Users\Isaia\Documents\3D Printing\Projects\Button\SD_BACKUP"
)
xcopy E:\ "C:\Users\Isaia\Documents\3D Printing\Projects\Button\SD_BACKUP\" /E /H /C /I /Y
echo Backup created successfully!

echo.
echo Step 2: Reorganizing Folder 18 (Button N - Nada/Nadowie/Noah)...
echo Current: REC at 1,2,5 and TTS at 3,4
echo Target:  REC at 1,2,3 and TTS at 4,5

cd /d E:\18
if exist 003.mp3 ren 003.mp3 003_temp.mp3
if exist 004.mp3 ren 004.mp3 004_temp.mp3
if exist 005.mp3 ren 005.mp3 003.mp3
if exist 003_temp.mp3 ren 003_temp.mp3 004.mp3
if exist 004_temp.mp3 ren 004_temp.mp3 005.mp3
echo Folder 18 reorganized: REC=1-3, TTS=4-5

echo.
echo Step 3: Reorganizing Folder 23 (Button S - Susu)...
echo Current: TTS at 1-9, REC at 10
echo Target:  REC at 1, TTS at 2-10

cd /d E:\23
if exist 010.mp3 ren 010.mp3 001_temp.mp3

REM Shift TTS files up by 1 position (in reverse order to avoid conflicts)
if exist 009.mp3 ren 009.mp3 010.mp3
if exist 008.mp3 ren 008.mp3 009.mp3
if exist 007.mp3 ren 007.mp3 008.mp3
if exist 006.mp3 ren 006.mp3 007.mp3
if exist 005.mp3 ren 005.mp3 006.mp3
if exist 004.mp3 ren 004.mp3 005.mp3
if exist 003.mp3 ren 003.mp3 004.mp3
if exist 002.mp3 ren 002.mp3 003.mp3
if exist 001.mp3 ren 001.mp3 002.mp3

REM Move Susu to position 1
if exist 001_temp.mp3 ren 001_temp.mp3 001.mp3
echo Folder 23 reorganized: REC=1, TTS=2-10

echo.
echo Step 4: Updating SPACE button reference...
cd /d E:\23
echo SPACE button now uses track 8 (was track 7)
echo Update your code if needed: SPACE uses S button TTS track 8

echo.
echo ===============================================================================
echo SD CARD REORGANIZATION COMPLETE!
echo ===============================================================================
echo.
echo REORGANIZED FOLDERS:
echo - Folder 18 (N): REC=1-3 (Nada,Nadowie,Noah), TTS=4-5 (Net,No)
echo - Folder 23 (S): REC=1 (Susu), TTS=2-10 (Sad,Scarf,Shoes,Sinemet,Sleep,Socks,Space,Stop,Sun)
echo.
echo NEXT STEPS:
echo 1. Upload the updated Arduino code
echo 2. Test priority mode switching with triple-press Period
echo 3. Verify different audio plays in HUMAN_FIRST vs GENERATED_FIRST modes
echo.
echo The priority mode system should now work with real audio differences!
echo.
pause
