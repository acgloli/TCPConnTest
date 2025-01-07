@echo off
chcp 65001
echo TCP服务器启动脚本

rem 检测系统架构
if "%PROCESSOR_ARCHITECTURE%"=="AMD64" (
    set "BINARY=TCPConnTest_server_Windows_x64.exe"
) else if "%PROCESSOR_ARCHITECTURE%"=="x86" (
    set "BINARY=TCPConnTest_server_Windows_x86.exe"
) else (
    echo 不支持的架构: %PROCESSOR_ARCHITECTURE%
    pause
    exit /b 1
)

set "PORT=9998"
set "MAX_CLIENTS=65535"

set /p "PORT=请输入端口号(默认%PORT%): "
set /p "MAX_CLIENTS=请输入最大连接数(默认%MAX_CLIENTS%): "

echo 正在启动服务器...
echo 架构: %PROCESSOR_ARCHITECTURE%
echo 监听端口: %PORT%
echo 最大连接数: %MAX_CLIENTS%

%BINARY% --host 0.0.0.0 --port "%PORT%" --max-clients "%MAX_CLIENTS%"
pause 