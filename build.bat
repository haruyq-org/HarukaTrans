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
 main.py

echo.
echo Build complete.
pause