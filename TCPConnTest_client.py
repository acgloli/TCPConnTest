import asyncio
import argparse
import time
import logging
import sys
import subprocess
import os

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

class MaxLevelFilter(logging.Filter):
    """只允许指定级别及以下的日志通过"""
    def __init__(self, max_level):
        super().__init__()
        self.max_level = max_level

    def filter(self, record):
        return record.levelno <= self.max_level

def set_file_limit(limit: int) -> None:
    """设置文件描述符限制"""
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        if sys.platform != 'win32':  # Windows不支持设置文件描述符限制
            if limit > soft:
                if limit <= hard:
                    resource.setrlimit(resource.RLIMIT_NOFILE, (limit, hard))
                    logging.info(f"已将文件描述符限制设置为 {limit}")
                else:
                    logging.warning(f"请求的文件描述符数量 {limit} 超过系统硬限制 {hard}")
                    limit = hard
                    resource.setrlimit(resource.RLIMIT_NOFILE, (limit, hard))
                    logging.info(f"已将文件描述符限制设置为最大值 {limit}")
    except Exception as e:
        logging.warning(f"设置文件描述符限制失败: {e}")

def parse_args():
    parser = argparse.ArgumentParser(description="持续TCP连接测试客户端（无限制版，实时显示）")
    parser.add_argument('--server_ip', type=str, required=True, help='目标服务器的IP地址')
    parser.add_argument('--server_port', type=int, default=9999, help='目标服务器的端口号（默认为9999）')
    parser.add_argument('--interval', type=float, default=0.0001, help='每次连接尝试的间隔时间（秒，默认为0.0001秒）')
    parser.add_argument('--report_interval', type=float, default=1.0, help='报告统计信息的间隔时间（秒，默认为1秒）')
    parser.add_argument('--error_log', type=str, default='error.log', help='错误日志文件名（默认为error.log）')
    parser.add_argument('--file-limit', type=int, default=65535, help='文件描述符限制（默认为65535）')
    return parser.parse_args()

def setup_logging(error_log_file):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # 设置最低日志级别

    # 创建控制台处理器，显示INFO及以下级别的日志
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.addFilter(MaxLevelFilter(logging.INFO))
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    # 创建文件处理器，记录ERROR及以上级别的日志
    file_handler = logging.FileHandler(error_log_file)
    file_handler.setLevel(logging.ERROR)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # 添加处理器到日志记录器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

class ConnectionManager:
    def __init__(self):
        self._connections = set()
        self._lock = asyncio.Lock()
        self._stats = {
            'success': 0,
            'failure': 0,
            'active': 0
        }
        self._stats_lock = asyncio.Lock()

    async def add_connection(self, writer: asyncio.StreamWriter) -> None:
        async with self._lock:
            self._connections.add(writer)
            async with self._stats_lock:
                self._stats['success'] += 1
                self._stats['active'] += 1

    async def remove_connection(self, writer: asyncio.StreamWriter) -> None:
        async with self._lock:
            if writer in self._connections:
                self._connections.remove(writer)
                async with self._stats_lock:
                    self._stats['active'] -= 1

    async def record_failure(self) -> None:
        async with self._stats_lock:
            self._stats['failure'] += 1

    def get_stats(self) -> dict:
        return {
            'success': self._stats['success'],
            'failure': self._stats['failure'],
            'active': self._stats['active']
        }

    def get_active_connections(self) -> set:
        return self._connections.copy()

async def create_connection(server_ip: str, server_port: int, 
                          connection_manager: ConnectionManager) -> None:
    try:
        reader, writer = await asyncio.open_connection(server_ip, server_port)
        await connection_manager.add_connection(writer)
        try:
            while True:
                # 保持连接活跃
                writer.write(b'ping')
                await writer.drain()
                data = await reader.read(100)
                if not data:
                    break
                await asyncio.sleep(60)  # 每分钟发送一次心跳
        except Exception as e:
            logging.error(f"连接维护时出错: {e}")
        finally:
            await connection_manager.remove_connection(writer)
            writer.close()
            await writer.wait_closed()
    except Exception as e:
        await connection_manager.record_failure()
        logging.error(f"连接到 {server_ip}:{server_port} 失败: {e}")

async def verify_connections(connection_manager: ConnectionManager) -> None:
    """定期验证连接状态"""
    while True:
        for writer in list(connection_manager.get_active_connections()):
            try:
                if writer.is_closing():
                    await connection_manager.remove_connection(writer)
            except Exception as e:
                logging.error(f"验证连接状态时出错: {e}")
        await asyncio.sleep(30)

async def report_status(connection_manager: ConnectionManager, report_interval: float) -> None:
    """报告连接状态"""
    while True:
        try:
            stats = connection_manager.get_stats()
            established = 0
            
            # 尝试不同的方式获取系统连接数
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
                    # 如果都不可用，尝试读取 /proc/net/tcp（仅Linux系统）
                    try:
                        with open('/proc/net/tcp', 'r') as f:
                            lines = f.readlines()[1:]  # 跳过标题行
                            established = sum(1 for line in lines 
                                           if line.split()[3] == '01')  # 01 表示 ESTABLISHED
                    except FileNotFoundError:
                        logging.warning("无法获取系统连接统计信息")
                        established = "未知"
            
            logging.info(
                f"连接统计:\n"
                f"成功建立连接: {stats['success']}\n"
                f"失败次数: {stats['failure']}\n"
                f"当前活动连接: {stats['active']}\n"
                f"系统ESTABLISHED连接: {established}"
            )
        except Exception as e:
            logging.error(f"生成状态报告时出错: {e}")
        await asyncio.sleep(report_interval)

async def main_async(server_ip: str, server_port: int, interval: float, 
                     report_interval: float, semaphore: asyncio.Semaphore) -> None:
    connection_manager = ConnectionManager()

    # 启动连接管理器
    manager_task = asyncio.create_task(
        connection_manager_task(server_ip, server_port, interval, 
                              connection_manager, semaphore)
    )

    # 启动状态报告任务
    reporter_task = asyncio.create_task(
        report_status(connection_manager, report_interval)
    )

    # 启动连接验证任务
    verify_task = asyncio.create_task(
        verify_connections(connection_manager)
    )

    try:
        await asyncio.gather(manager_task, reporter_task, verify_task)
    except Exception as e:
        logging.error(f"发生错误: {e}")
        # 清理所有连接
        for writer in connection_manager.get_active_connections():
            writer.close()

async def connection_manager_task(server_ip: str, server_port: int, interval: float,
                                connection_manager: ConnectionManager,
                                semaphore: asyncio.Semaphore) -> None:
    while True:
        async with semaphore:
            asyncio.create_task(
                create_connection(server_ip, server_port, connection_manager)
            )
        await asyncio.sleep(interval)

if __name__ == "__main__":
    args = parse_args()
    setup_logging(args.error_log)

    # 设置文件描述符限制
    set_file_limit(args.file_limit)

    semaphore = asyncio.Semaphore(1000)  # 限制最大并发连接数

    try:
        asyncio.run(main_async(
            args.server_ip,
            args.server_port,
            args.interval,
            args.report_interval,
            semaphore
        ))
    except KeyboardInterrupt:
        logging.info("\n测试结束，正在关闭所有连接...")
        sys.exit(0)
