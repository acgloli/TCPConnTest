TCPConnTest - TCP Connection Testing Tool
==============================

[中文](README.md) | [English](README_EN.md)

Introduction
-------
This tool was developed with AI assistance.

TCPConnTest is a specialized tool designed to test TCP server concurrent connection handling capabilities. It evaluates server and network maximum connection capacity by simulating multiple client connections simultaneously.

Disclaimer
-------
This tool is intended for network performance testing and system optimization only. Testing unauthorized systems or any form of network attacks is strictly prohibited.
By using this tool, you agree to:

1. Use only in authorized systems and network environments
2. Not use for any illegal purposes or malicious attacks
3. Comply with relevant laws and network security policies
4. Take full responsibility for any consequences of misuse

The author assumes no responsibility for any issues or damages caused by misuse of this tool.

Installation
-------
1. Install Python (3.7+)
   * Windows: Download from Python official website (https://www.python.org/downloads/)
   * Linux: sudo apt install python3 python3-pip (Ubuntu/Debian)
2. Install Dependencies
   * Windows: pip install -r requirements.txt
   * Linux: pip3 install -r requirements.txt

Usage
-------
Windows:
1. Server:
   - Double click run_server.bat
   - From source: python TCPConnTest_server.py --host 0.0.0.0 --port 9998 --max-clients 65535
   - Using binary: TCPConnTest_server_Windows_[x64/x86].exe --host 0.0.0.0 --port 9998 --max-clients 65535

2. Client:
   - Double click run_client.bat
   - From source: python TCPConnTest_client.py --server_ip <server_ip> --server_port 9998 --interval 0.001 --file-limit 65535
   - Using binary: TCPConnTest_client_Windows_[x64/x86].exe --server_ip <server_ip> --server_port 9998 --interval 0.001 --file-limit 65535

Linux:
1. Set permissions before first run:
   - From source: chmod +x *.py *.sh
   - Using binary: chmod +x TCPConnTest_* *.sh

2. Server:
   - Execute: ./run_server.sh
   - From source: python3 TCPConnTest_server.py --host 0.0.0.0 --port 9998 --max-clients 65535
   - Using binary: ./TCPConnTest_server_Linux_[x64/x86/arm64] --host 0.0.0.0 --port 9998 --max-clients 65535

3. Client:
   - Execute: ./run_client.sh
   - From source: python3 TCPConnTest_client.py --server_ip <server_ip> --server_port 9998 --interval 0.001 --file-limit 65535
   - Using binary: ./TCPConnTest_client_Linux_[x64/x86/arm64] --server_ip <server_ip> --server_port 9998 --interval 0.001 --file-limit 65535

Parameters
-------
Server Parameters:

--host: Listen address (default 0.0.0.0)

--port: Listen port (default 9998)

--max-clients: Maximum client connections (default 65535)

Client Parameters:

--server_ip: Server IP address (required)

--server_port: Server port (default 9998)

--interval: Connection interval (default 0.0001 seconds)

--report_interval: Status report interval (default 1 second)

--error_log: Error log filename (default error.log)

--file-limit: File descriptor limit (default 65535)

Notes
-------
1. Windows: Recommended to run with administrator privileges
2. Linux: Set execution permissions before first run
3. Ensure firewall allows program access
4. If port is occupied, use a different port

Common Issues
-------
1. Permission issues:
   * Windows: Run command prompt as administrator
   * Linux: Use sudo (e.g., sudo ./TCPConnTest_server)
2. Need higher concurrent connections:
   - Modify system limits (Linux)
   - Adjust firewall settings
   - Ensure sufficient system resources 