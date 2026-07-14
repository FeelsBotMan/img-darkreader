@echo off
call venv\Scripts\activate
python -m dark_reader %*
if errorlevel 1 pause
