@echo off
call venv\Scripts\activate
python -m run %*
if errorlevel 1 pause