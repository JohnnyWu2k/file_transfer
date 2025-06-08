@echo off
setlocal

:: ============================================================================
::  SETUP SCRIPT FOR THE PYTHON APPLICATION
::  This script ensures Python and required packages are installed,
::  then runs the main application.
:: ============================================================================

echo --- Setting up script environment...

:: Define file and directory paths based on the script's location.
set "SCRIPT_DIR=%~dp0src"
set "PYTHON_SCRIPT=%SCRIPT_DIR%\gui2.py"
set "REQUIREMENTS_FILE=%~dp0requirements.txt"

:: ----------------------------------------------------------------------------
:: 1. CHECK FOR PYTHON INSTALLATION
:: ----------------------------------------------------------------------------
echo.
echo --- Checking for Python installation...

python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo Python is not found in your system's PATH.
    echo Attempting to install Python 3 using winget...
    
    :: Use winget to install the latest stable version of Python 3.
    winget install --id Python.Python.3 -e --source winget
    
    IF ERRORLEVEL 1 (
        echo.
        echo [ERROR] Failed to install Python using winget.
        echo Please install Python 3 manually from: https://www.python.org/
        pause
        exit /b 1
    )
    echo Python installed successfully.
) ELSE (
    echo Python is already installed.
)

:: ----------------------------------------------------------------------------
:: 2. INSTALL REQUIRED PACKAGES
:: ----------------------------------------------------------------------------
echo.
echo --- Installing required packages from requirements.txt...

pip install -r "%REQUIREMENTS_FILE%"
if ERRORLEVEL 1 (
    echo.
    echo [ERROR] Failed to install required packages.
    echo Please check your internet connection and ensure pip is working correctly.
    pause
    exit /b 1
)
echo All required packages are installed.

:: ----------------------------------------------------------------------------
:: 3. RUN THE PYTHON APPLICATION
:: ----------------------------------------------------------------------------
echo.
echo --- Starting the Python application...
echo.

cls

python "%PYTHON_SCRIPT%"

:: ----------------------------------------------------------------------------
:: 4. CLEANUP
:: ----------------------------------------------------------------------------
echo.
echo --- Script has finished. Press any key to close this window. ---
endlocal
pause >nul