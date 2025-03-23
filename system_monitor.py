import os
import time
import psutil
import logging
from config import logger


class SystemMonitor:
    def __init__(self):
        self.start_time = time.time()
        logger.info("System monitor initialized")

    def get_cpu_usage(self):
        """Get CPU usage percentage as integer"""
        return int(psutil.cpu_percent())

    def get_memory_usage(self):
        """Get memory usage percentage as integer"""
        return int(psutil.virtual_memory().percent)

    def get_storage_usage(self):
        """Get storage usage percentage as integer"""
        return int(psutil.disk_usage('/').percent)

    def get_uptime(self):
        """Get system uptime in format 'Xd Xh Xm Xs'"""
        uptime_seconds = time.time() - self.start_time
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        uptime_str = ""
        if days > 0:
            uptime_str += f"{int(days)}d "
        if hours > 0 or days > 0:
            uptime_str += f"{int(hours)}h "
        if minutes > 0 or hours > 0 or days > 0:
            uptime_str += f"{int(minutes)}m "
        uptime_str += f"{int(seconds)}s"

        return uptime_str.strip()

    def get_metrics(self):
        """Get all system metrics at once"""
        return {
            "cpu_usage": self.get_cpu_usage(),
            "memory_usage": self.get_memory_usage(),
            "storage_usage": self.get_storage_usage(),
            "uptime": self.get_uptime()
        }
