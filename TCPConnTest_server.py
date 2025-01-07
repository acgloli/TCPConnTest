# async_tcp_server_optimized.py

import asyncio
import logging
import signal
import argparse
from typing import Set, Dict
from dataclasses import dataclass
import time
import socket
import subprocess
import os
import sys

# 根据操作系统选择性导入 resource 模块
if os.name != 'nt':  # 如果不是 Windows 系统
    import resource
else:
    # Windows 系统下模拟 resource 模块的必要功能
    class DummyResource:
        def getrlimit(self, _):
            return (65535, 65535)
        
        def setrlimit(self, _, limits):
            pass
        
        RLIMIT_NOFILE = -1
    
    resource = DummyResource()

@dataclass
class ServerStats:
    """服务器统计信息"""
    start_time: float
    total_connections: int = 0
    active_connections: int = 0
    bytes_received: int = 0
    bytes_sent: int = 0

class TCPServer:
    def __init__(self, host: str, port: int, max_clients: int = 10000):
        self.host = host
        self.port = port
        self.max_clients = max_clients
        
        # 设置系统文件描述符限制
        try:
            soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            # 计算所需的文件描述符数量（每个连接大约需要2个）
            required_fd = max_clients * 2 + 50  # 额外预留一些
            
            if sys.platform != 'win32':  # Windows不支持设置文件描述符限制
                if required_fd > soft:
                    if required_fd <= hard:
                        resource.setrlimit(resource.RLIMIT_NOFILE, (required_fd, hard))
                        logging.info(f"已将文件描述符限制设置为 {required_fd}")
                    else:
                        logging.warning(f"所需文件描述符数量 {required_fd} 超过系统硬限制 {hard}")
                        self.max_clients = (hard - 50) // 2  # 调整最大客户端数
                        logging.warning(f"已将最大客户端数调整为 {self.max_clients}")
        except Exception as e:
            logging.warning(f"设置文件描述符限制失败: {e}")

        self.stats = ServerStats(start_time=time.time())
        self.clients: Set[asyncio.StreamWriter] = set()
        self.server = None
        self.client_info: Dict[asyncio.StreamWriter, Dict] = {}
        self.connection_limiter = asyncio.Semaphore(self.max_clients)
        self._stats_lock = asyncio.Lock()
        self._cleanup_lock = asyncio.Lock()
        self._shutdown = False  # 添加关闭标志
        self._tasks = set()  # 添加任务集合

    async def _update_stats(self, connection_added: bool = True) -> None:
        """原子性地更新统计信息"""
        async with self._stats_lock:
            if connection_added:
                self.stats.total_connections += 1
                self.stats.active_connections += 1
            else:
                self.stats.active_connections -= 1

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """处理单个客户端连接"""
        if len(self.clients) >= self.max_clients:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            return
        
        async with self.connection_limiter:
            addr = writer.get_extra_info('peername')
            
            try:
                async with self._cleanup_lock:
                    if len(self.clients) >= self.max_clients:  # 双重检查
                        raise RuntimeError("超过最大连接数限制")
                        
                    self.clients.add(writer)
                    await self._update_stats(True)
                    self.client_info[writer] = {
                        'connected_at': time.time(),
                        'addr': addr,
                        'bytes_received': 0,
                        'bytes_sent': 0
                    }
                
                logging.info(f"新连接来自 {addr}，当前活动连接数: {self.stats.active_connections}")
                
                while True:
                    try:
                        data = await asyncio.wait_for(reader.read(8192), timeout=300)
                        if not data:
                            break
                        
                        self.client_info[writer]['bytes_received'] += len(data)
                        self.stats.bytes_received += len(data)
                        
                        writer.write(data)
                        await writer.drain()
                        
                        self.client_info[writer]['bytes_sent'] += len(data)
                        self.stats.bytes_sent += len(data)
                        
                    except asyncio.TimeoutError:
                        logging.warning(f"客户端 {addr} 超时")
                        break
                        
            except ConnectionError:
                logging.info(f"客户端 {addr} 断开连接")
            except Exception as e:
                logging.error(f"处理客户端 {addr} 时出错: {e}", exc_info=True)
            finally:
                await self.cleanup_client(writer)

    async def cleanup_client(self, writer: asyncio.StreamWriter) -> None:
        """清理客户端连接"""
        async with self._cleanup_lock:
            addr = writer.get_extra_info('peername')
            if writer in self.clients:
                self.clients.remove(writer)
                await self._update_stats(False)
                client_stats = self.client_info.pop(writer, {})
                duration = time.time() - client_stats.get('connected_at', time.time())
                logging.info(
                    f"客户端 {addr} 断开连接。"
                    f"连接持续时间: {duration:.2f}秒, "
                    f"接收: {client_stats.get('bytes_received', 0)} 字节, "
                    f"发送: {client_stats.get('bytes_sent', 0)} 字节"
                )
            try:
                writer.close()
                await writer.wait_closed()  # 等待连接完全关闭
            except Exception as e:
                logging.error(f"关闭连接 {addr} 时出错: {e}")

    async def verify_connections(self) -> None:
        """定期验证连接状态"""
        while True:
            async with self._cleanup_lock:
                # 验证所有连接是否还有效
                for writer in list(self.clients):
                    try:
                        if writer.is_closing():
                            await self.cleanup_client(writer)
                    except Exception as e:
                        logging.error(f"验证连接状态时出错: {e}")
            await asyncio.sleep(30)  # 每30秒检查一次

    async def start(self) -> None:
        """启动服务器"""
        if self.server:
            return
            
        try:
            self.server = await asyncio.start_server(
                self.handle_client,
                self.host,
                self.port,
                reuse_address=True,
                reuse_port=hasattr(socket, 'SO_REUSEPORT'),
                backlog=min(self.max_clients, 2048),  # 限制积压连接数
                start_serving=False  # 手动控制开始服务
            )
            
            # 启动后台任务
            self._tasks.add(asyncio.create_task(self.report_stats()))
            self._tasks.add(asyncio.create_task(self.verify_connections()))
            
            async with self.server:
                await self.server.start_serving()
                addrs = ', '.join(str(sock.getsockname()) for sock in self.server.sockets)
                logging.info(f"服务器启动，监听地址: {addrs}")
                
                try:
                    await asyncio.Future()  # 永久等待，直到被取消
                except asyncio.CancelledError:
                    logging.info("服务器收到取消信号")
                    raise
                    
        except Exception as e:
            logging.error(f"服务器启动失败: {e}")
            raise

    async def stop(self) -> None:
        """关闭服务器"""
        if self._shutdown:  # 防止重复关闭
            return
        
        self._shutdown = True
        logging.info("正在关闭服务器...")

        # 1. 首先停止接受新连接
        if self.server:
            self.server.close()
            try:
                await self.server.wait_closed()
            except Exception as e:
                logging.error(f"关闭服务器时出错: {e}")

        # 2. 取消所有后台任务
        for task in list(self._tasks):
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logging.error(f"取消任务时出错: {e}")
        self._tasks.clear()

        # 3. 关闭所有现有客户端连接
        if self.clients:
            close_tasks = []
            for writer in list(self.clients):
                try:
                    if not writer.is_closing():
                        writer.close()
                        close_tasks.append(writer.wait_closed())
                except Exception as e:
                    logging.error(f"关闭客户端连接时出错: {e}")
            
            if close_tasks:
                try:
                    await asyncio.gather(*close_tasks, return_exceptions=True)
                except Exception as e:
                    logging.error(f"等待连接关闭时出错: {e}")
            
            self.clients.clear()
            self.client_info.clear()

        logging.info("服务器已完全关闭")

    async def report_stats(self, interval: int = 60) -> None:
        """定期报告服务器状态"""
        while True:
            try:
                # 尝试不同的方式获取连接统计
                established = 0
                try:
                    # 首先尝试 ss 命令（新系统常用）
                    result = subprocess.run(['ss', '-tn', 'state', 'established'], 
                                         capture_output=True, text=True)
                    established = len(result.stdout.strip().split('\n')) - 1
                except FileNotFoundError:
                    try:
                        # 然后尝试 netstat 命令
                        result = subprocess.run(['netstat', '-ant'], 
                                             capture_output=True, text=True)
                        established = result.stdout.count('ESTABLISHED')
                    except FileNotFoundError:
                        # 如果都不可用，使用 /proc/net/tcp
                        try:
                            with open('/proc/net/tcp', 'r') as f:
                                lines = f.readlines()[1:]  # 跳过标题行
                                established = sum(1 for line in lines 
                                               if line.split()[3] == '01')  # 01 表示 ESTABLISHED
                        except FileNotFoundError:
                            logging.warning("无法获取系统连接统计信息")
                
                uptime = time.time() - self.stats.start_time
                logging.info(
                    f"服务器状态报告:\n"
                    f"运行时间: {uptime:.2f}秒\n"
                    f"总连接数: {self.stats.total_connections}\n"
                    f"当前活动连接: {self.stats.active_connections}\n"
                    f"系统ESTABLISHED连接: {established}\n"
                    f"总接收字节: {self.stats.bytes_received}\n"
                    f"总发送字节: {self.stats.bytes_sent}"
                )
            except Exception as e:
                logging.error(f"生成状态报告时出错: {e}")
            
            await asyncio.sleep(interval)

def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="异步TCP服务器")
    parser.add_argument('--host', default='0.0.0.0', help='监听地址')
    parser.add_argument('--port', type=int, default=9998, help='监听端口')
    parser.add_argument('--max-clients', type=int, default=10000, help='最大客户端连接数')
    return parser.parse_args()

async def main() -> None:
    """主函数"""
    args = parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    server = TCPServer(args.host, args.port, args.max_clients)
    
    def handle_signal():
        """处理信号"""
        if not server._shutdown:  # 防止重复处理信号
            logging.info("接收到关闭信号，正在关闭服务器...")
            # 取消当前运行的任务
            for task in asyncio.all_tasks():
                if task is not asyncio.current_task():
                    task.cancel()

    # 设置信号处理
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, handle_signal)
        except NotImplementedError:
            # Windows 系统使用备用方案
            signal.signal(sig, lambda s, f: handle_signal())
    
    try:
        await server.start()
    except asyncio.CancelledError:
        await server.stop()
    except KeyboardInterrupt:
        await server.stop()
    except Exception as e:
        logging.error(f"服务器运行时出错: {e}", exc_info=True)
        await server.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # 优雅地处理 Ctrl+C
