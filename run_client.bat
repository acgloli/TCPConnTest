@echo off
chcp 65001
echo TCP客户端启动脚本

rem 检测系统架构
if "%PROCESSOR_ARCHITECTURE%"=="AMD64" (
    set "BINARY=TCPConnTest_client_Windows_x64.exe"
) else if "%PROCESSOR_ARCHITECTURE%"=="x86" (
    set "BINARY=TCPConnTest_client_Windows_x86.exe"
) else (
    echo 不支持的架构: %PROCESSOR_ARCHITECTURE%
    pause
    exit /b 1
)

set "SERVER_IP="
set "PORT=9998"
set "INTERVAL=0.001"

set /p "SERVER_IP=请输入服务器IP: "
set /p "PORT=请输入服务器端口(默认%PORT%): "
set /p "INTERVAL=请输入连接间隔(默认%INTERVAL%): "

if "%SERVER_IP%"=="" (
    echo 错误：服务器IP不能为空！
    pause
    exit /b 1
)

echo 正在启动客户端...
echo 架构: %PROCESSOR_ARCHITECTURE%
echo 连接到服务器: %SERVER_IP%:%PORT%

%BINARY% --server_ip "%SERVER_IP%" --server_port "%PORT%" --interval "%INTERVAL%"
pause 