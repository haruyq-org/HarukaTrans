@echo off
cd /d %~dp0

python -m venv .venv
call .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

call .venv\Scripts\deactivate

cls

echo ========================
echo Setup completed.
echo ========================

pause