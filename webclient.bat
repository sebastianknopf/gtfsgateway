@echo off

if not exist ".\\venv" (
    call install.bat
)

call venv/Scripts/activate

start "" http://127.0.0.1:5000
python -m webclient