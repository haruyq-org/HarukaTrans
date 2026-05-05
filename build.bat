@echo off

.\.venv\Scripts\pyinstaller.exe ^
 --clean ^
 --noconfirm ^
 --onefile ^
 --name "HarukaTrans" ^
 --icon "assets/icon.ico" ^
 --collect-data "flet" ^
 --add-data "vad/silero_vad.onnx;vad" ^
 --add-data "assets/icon.ico;assets" ^
 --exclude-module rich ^
 src/main.py

echo.

.\.venv\Scripts\pyinstaller.exe ^
 --clean ^
 --noconfirm ^
 --onefile ^
 --name "updater" ^
 --collect-data "src/updater" ^
 src/updater/updater.py

echo.
echo Build complete.
pause