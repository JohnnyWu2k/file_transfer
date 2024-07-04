@echo off
REM 获取当前批处理文件所在的目录
set CURRENT_DIR=%~dp0

REM 设置Python脚本的环境变量
set PYTHON_SCRIPT=%CURRENT_DIR%gui2.py

REM 运行Python脚本
python %PYTHON_SCRIPT%
