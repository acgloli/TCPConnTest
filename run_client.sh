#!/bin/bash

echo "TCP客户端启动脚本"

# 检测系统架构
ARCH=$(uname -m)
case ${ARCH} in
    x86_64)
        BINARY="TCPConnTest_client_Linux_x64"
        ;;
    i386|i686)
        BINARY="TCPConnTest_client_Linux_x86"
        ;;
    aarch64)
        BINARY="TCPConnTest_client_Linux_arm64"
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
INTERVAL=0.001
FILE_LIMIT=65535

# 获取服务器IP（必填）
while [ -z "$SERVER_IP" ]; do
    read -p "请输入服务器IP: " SERVER_IP
    if [ -z "$SERVER_IP" ]; then
        echo "错误：服务器IP不能为空！"
    fi
done

# 获取其他参数
read -p "请输入服务器端口(默认${PORT}): " input_port
read -p "请输入连接间隔(默认${INTERVAL}): " input_interval
read -p "请输入文件描述符限制(默认${FILE_LIMIT}): " input_file_limit

# 如果用户有输入，则使用用户输入的值
if [ ! -z "$input_port" ]; then
    PORT=$input_port
fi

if [ ! -z "$input_interval" ]; then
    INTERVAL=$input_interval
fi

if [ ! -z "$input_file_limit" ]; then
    FILE_LIMIT=$input_file_limit
fi

echo "正在启动客户端..."
echo "架构: ${ARCH}"
echo "连接到服务器: ${SERVER_IP}:${PORT}"
echo "连接间隔: ${INTERVAL}"
echo "文件描述符限制: ${FILE_LIMIT}"

# 运行客户端
./${BINARY} --server_ip "${SERVER_IP}" --server_port "${PORT}" \
           --interval "${INTERVAL}" --file-limit "${FILE_LIMIT}" 