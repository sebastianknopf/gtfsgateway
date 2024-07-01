@echo off

start "" http://127.0.0.1:5000

call venv/Scripts/activate.bat
python -m webclient