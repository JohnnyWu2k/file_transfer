@echo off
setlocal

REM 设置Python脚本的环境变量
set SCRIPT_DIR=%~dp0
set PYTHON_SCRIPT=%SCRIPT_DIR%gui2.py
set REQUIREMENTS_FILE=%SCRIPT_DIR%requirements.txt

REM 检查是否已安装Python
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo Python is not installed. Installing Python using winget...
    winget install --id 9NRWMJP3717K
    if ERRORLEVEL 1 (
        echo Failed to install Python. Please install Python manually from https://www.python.org/.
        pause
        exit /b 1
    )
)

REM 安装所需包
pip install -r %REQUIREMENTS_FILE%
if ERRORLEVEL 1 (
    echo Failed to install required packages. Please ensure you have pip installed and try again.
    pause
    exit /b 1
)

REM 运行Python脚本
python %PYTHON_SCRIPT%

endlocal
pause
