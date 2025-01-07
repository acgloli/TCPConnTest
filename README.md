TCPConnTest - TCP连接数测试工具
==============================

[中文](README.md) | [English](README_EN.md)

简介
-------
本工具由 AI 辅助开发。

TCPConnTest 是一个专门用于测试 TCP 服务器并发连接处理能力的工具。它通过模拟大量客户端同时建立 TCP 连接，评估服务器及网络的最大连接承载能力。


免责声明
-------
本工具仅供网络性能测试和系统调优使用。严禁用于对未经授权的系统进行测试或任何形式的网络攻击。
使用本工具即表示您同意：

1. 仅在授权的系统和网络环境中使用
2. 不用于任何非法用途或恶意攻击
3. 遵守相关法律法规和网络安全政策
4. 对因违规使用造成的任何后果自行承担责任

作者不对任何因滥用本工具导致的问题或损失负责。

安装说明
-------
1. 安装 Python (3.7+)
   * Windows: 从 Python官网(https://www.python.org/downloads/) 下载安装
   * Linux: sudo apt install python3 python3-pip (Ubuntu/Debian)
2. 安装依赖库
   * Windows: pip install -r requirements.txt
   * Linux: pip3 install -r requirements.txt

运行方法
-------
Windows系统:
1. 服务端运行：
   - 双击 run_server.bat
   - 从源码运行：python TCPConnTest_server.py --host 0.0.0.0 --port 9998 --max-clients 65535
   - 使用编译版：TCPConnTest_server_Windows_[x64/x86].exe --host 0.0.0.0 --port 9998 --max-clients 65535

2. 客户端运行：
   - 双击 run_client.bat
   - 从源码运行：python TCPConnTest_client.py --server_ip <服务器IP> --server_port 9998 --interval 0.001 --file-limit 65535
   - 使用编译版：TCPConnTest_client_Windows_[x64/x86].exe --server_ip <服务器IP> --server_port 9998 --interval 0.001 --file-limit 65535

Linux系统:
1. 首次运行前设置权限：
   - 从源码运行：chmod +x *.py *.sh
   - 使用编译版：chmod +x TCPConnTest_* *.sh

2. 服务端运行：
   - 执行：./run_server.sh
   - 从源码运行：python3 TCPConnTest_server.py --host 0.0.0.0 --port 9998 --max-clients 65535
   - 使用编译版：./TCPConnTest_server_Linux_[x64/x86/arm64] --host 0.0.0.0 --port 9998 --max-clients 65535

3. 客户端运行：
   - 执行：./run_client.sh
   - 从源码运行：python3 TCPConnTest_client.py --server_ip <服务器IP> --server_port 9998 --interval 0.001 --file-limit 65535
   - 使用编译版：./TCPConnTest_client_Linux_[x64/x86/arm64] --server_ip <服务器IP> --server_port 9998 --interval 0.001 --file-limit 65535

参数说明
-------
服务端参数：

--host: 监听地址（默认 0.0.0.0）

--port: 监听端口（默认 9998）

--max-clients: 最大客户端连接数（默认 65535）

客户端参数：

--server_ip: 服务器IP地址（必填）

--server_port: 服务器端口（默认 9998）

--interval: 连接间隔时间（默认 0.0001秒）

--report_interval: 状态报告间隔（默认 1秒）

--error_log: 错误日志文件名（默认 error.log）

--file-limit: 文件描述符限制（默认 65535）

注意事项
-------
1. Windows系统建议使用管理员权限运行
2. Linux系统首次运行前需要设置执行权限
3. 确保防火墙允许程序通过
4. 如果端口被占用，请更换其他端口

常见问题
-------
1. 遇到权限问题：
   * Windows: 以管理员身份运行命令提示符
   * Linux: 使用sudo运行（例：sudo ./TCPConnTest_server）
2. 需要更高的并发连接数：
   - 修改系统限制（Linux）
   - 调整防火墙设置
   - 确保有足够的系统资源