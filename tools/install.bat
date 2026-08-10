@echo off
REM Yahoo Mail Assistant - one-click setup for Windows
REM Downloads yahoo_mail.py and runs it.
title Yahoo Mail Assistant

echo ============================================
echo   YAHOO MAIL ASSISTANT - SETUP
echo ============================================
echo.

REM --- Check Python is installed ---
where python >nul 2>nul
if %errorlevel%==0 (
    set PYTHON=python
    goto :havepython
)
where py >nul 2>nul
if %errorlevel%==0 (
    set PYTHON=py
    goto :havepython
)

echo   Python 3 is not installed or not on PATH.
echo.
echo   You need Python to run this tool.
echo.
echo   Options:
echo     1. Download Python from https://python.org/downloads
echo        IMPORTANT: check "Add python.exe to PATH" during install.
echo     2. After installing, reopen this file (or a terminal) and run:
echo          python yahoo_mail.py
echo.
pause
exit /b 1

:havepython
echo   Found Python. Checking version...
%PYTHON% --version
echo.

REM --- Download the tool if not already present ---
if not exist "yahoo_mail.py" (
    echo   Downloading yahoo_mail.py...
    curl.exe -sSL -o yahoo_mail.py "https://raw.githubusercontent.com/DezzyWxL/legacy-releases/main/tools/yahoo_mail.py"
    if %errorlevel% neq 0 (
        echo   Download failed. Check your internet connection.
        echo   Or download manually and save as yahoo_mail.py next to this file.
        pause
        exit /b 1
    )
) else (
    echo   yahoo_mail.py already present. Skipping download.
)

echo.
echo   Launching Yahoo Mail Assistant...
echo.
%PYTHON% yahoo_mail.py

echo.
echo   Session ended. Press any key to close.
pause >nul
