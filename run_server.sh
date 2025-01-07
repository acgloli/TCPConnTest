#!/bin/bash

echo "TCP服务器启动脚本"

# 检测系统架构
ARCH=$(uname -m)
case ${ARCH} in
    x86_64)
        BINARY="TCPConnTest_server_Linux_x64"
        ;;
    i386|i686)
        BINARY="TCPConnTest_server_Linux_x86"
        ;;
    aarch64)
        BINARY="TCPConnTest_server_Linux_arm64"
        ;;
    *)
        echo "不支持的架构: ${ARCH}"
        exit 1
        ;;
esac

# 检查二进制文件是否存在
if [ ! -f "./${BINARY}" ]; then
    echo "错误：找不到文件 ${BINARY}"
    exit 1
fi

# 添加执行权限
chmod +x "./${BINARY}"

# 设置默认值
PORT=9998
MAX_CLIENTS=65535

# 获取用户输入
read -p "请输入端口号(默认${PORT}): " input_port
read -p "请输入最大连接数(默认${MAX_CLIENTS}): " input_max_clients

# 如果用户有输入，则使用用户输入的值
if [ ! -z "$input_port" ]; then
    PORT=$input_port
fi

if [ ! -z "$input_max_clients" ]; then
    MAX_CLIENTS=$input_max_clients
fi

echo "正在启动服务器..."
echo "架构: ${ARCH}"
echo "监听端口: ${PORT}"
echo "最大连接数: ${MAX_CLIENTS}"

# 运行服务器
./${BINARY} --host 0.0.0.0 --port "${PORT}" --max-clients "${MAX_CLIENTS}" 