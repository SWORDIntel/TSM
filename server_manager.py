#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLASSIFICATION: TOP SECRET
PROJECT: TSM (Telegram Session Manager)
MODULE: Server Process Manager
AUTHOR: ARCHITECT
CREATED: 2025-07-27

Robust server process management with health checks, isolation, and clean teardown.
Supports multiple server types including gRPC, mock servers, and microservices.
"""

import asyncio
import json
import logging
import os
import psutil
import signal
import socket
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from threading import Thread, Event, Lock
import grpc
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)-15s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("ServerManager")


class ServerStatus(Enum):
    """Server status enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"
    UNHEALTHY = "unhealthy"


class HealthCheckType(Enum):
    """Types of health checks"""
    TCP = "tcp"
    HTTP = "http"
    GRPC = "grpc"
    CUSTOM = "custom"


@dataclass
class ServerConfig:
    """Configuration for a managed server"""
    name: str
    command: List[str]
    working_dir: Optional[Path] = None
    env_vars: Dict[str, str] = field(default_factory=dict)
    port: Optional[int] = None
    host: str = "localhost"
    startup_timeout: float = 30.0
    shutdown_timeout: float = 10.0
    health_check_interval: float = 5.0
    health_check_timeout: float = 2.0
    health_check_type: HealthCheckType = HealthCheckType.TCP
    health_check_endpoint: Optional[str] = None
    max_restarts: int = 3
    restart_delay: float = 5.0
    log_file: Optional[Path] = None
    stdout_handler: Optional[Callable[[str], None]] = None
    stderr_handler: Optional[Callable[[str], None]] = None
    pre_start_hook: Optional[Callable[[], None]] = None
    post_start_hook: Optional[Callable[[], None]] = None
    pre_stop_hook: Optional[Callable[[], None]] = None
    post_stop_hook: Optional[Callable[[], None]] = None


@dataclass
class ServerMetrics:
    """Metrics for a managed server"""
    start_time: Optional[datetime] = None
    stop_time: Optional[datetime] = None
    restart_count: int = 0
    total_uptime: timedelta = timedelta()
    last_health_check: Optional[datetime] = None
    health_check_failures: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'stop_time': self.stop_time.isoformat() if self.stop_time else None,
            'restart_count': self.restart_count,
            'total_uptime_seconds': self.total_uptime.total_seconds(),
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'health_check_failures': self.health_check_failures,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage
        }


class HealthChecker(ABC):
    """Abstract base class for health checkers"""
    
    @abstractmethod
    async def check(self, config: ServerConfig) -> bool:
        """Perform health check"""
        pass


class TCPHealthChecker(HealthChecker):
    """TCP port connectivity health checker"""
    
    async def check(self, config: ServerConfig) -> bool:
        if not config.port:
            return True
            
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(config.host, config.port),
                timeout=config.health_check_timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            return False


class GRPCHealthChecker(HealthChecker):
    """gRPC service health checker"""
    
    async def check(self, config: ServerConfig) -> bool:
        if not config.port:
            return True
            
        try:
            channel = grpc.aio.insecure_channel(f'{config.host}:{config.port}')
            await asyncio.wait_for(
                channel.channel_ready(),
                timeout=config.health_check_timeout
            )
            await channel.close()
            return True
        except asyncio.TimeoutError:
            return False


class ManagedServer:
    """Represents a single managed server process"""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.status = ServerStatus.STOPPED
        self.metrics = ServerMetrics()
        self._health_checker = self._create_health_checker()
        self._health_check_task: Optional[asyncio.Task] = None
        self._stdout_reader: Optional[Thread] = None
        self._stderr_reader: Optional[Thread] = None
        self._stop_event = Event()
        self._lock = Lock()
        
    def _create_health_checker(self) -> HealthChecker:
        """Create appropriate health checker based on config"""
        if self.config.health_check_type == HealthCheckType.TCP:
            return TCPHealthChecker()
        elif self.config.health_check_type == HealthCheckType.GRPC:
            return GRPCHealthChecker()
        else:
            return TCPHealthChecker()  # Default fallback
    
    def _stream_reader(self, stream, handler: Optional[Callable], is_stderr: bool = False):
        """Read from process stream and handle output"""
        prefix = "STDERR" if is_stderr else "STDOUT"
        try:
            for line in iter(stream.readline, b''):
                if self._stop_event.is_set():
                    break
                line_str = line.decode('utf-8', errors='replace').rstrip()
                if line_str:
                    logger.debug(f"[{self.config.name}] {prefix}: {line_str}")
                    if handler:
                        handler(line_str)
        except Exception as e:
            logger.error(f"Error reading {prefix} for {self.config.name}: {e}")
    
    async def start(self) -> bool:
        """Start the server process"""
        with self._lock:
            if self.status == ServerStatus.RUNNING:
                logger.warning(f"Server {self.config.name} is already running")
                return True
            
            self.status = ServerStatus.STARTING
            logger.info(f"Starting server: {self.config.name}")
            
            # Pre-start hook
            if self.config.pre_start_hook:
                try:
                    self.config.pre_start_hook()
                except Exception as e:
                    logger.error(f"Pre-start hook failed for {self.config.name}: {e}")
                    self.status = ServerStatus.FAILED
                    return False
            
            # Prepare environment
            env = os.environ.copy()
            env.update(self.config.env_vars)
            
            # Prepare startup command
            cmd = self.config.command
            cwd = self.config.working_dir or Path.cwd()
            
            # Setup log files
            stdout_file = None
            stderr_file = None
            if self.config.log_file:
                log_dir = self.config.log_file.parent
                log_dir.mkdir(parents=True, exist_ok=True)
                stdout_file = open(f"{self.config.log_file}.stdout", 'a')
                stderr_file = open(f"{self.config.log_file}.stderr", 'a')
            
            try:
                # Start the process
                self.process = subprocess.Popen(
                    cmd,
                    cwd=cwd,
                    env=env,
                    stdout=subprocess.PIPE if not stdout_file else stdout_file,
                    stderr=subprocess.PIPE if not stderr_file else stderr_file,
                    preexec_fn=os.setsid if sys.platform != 'win32' else None,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
                )
                
                self.metrics.start_time = datetime.now()
                
                # Start output readers if needed
                if not stdout_file:
                    self._stdout_reader = Thread(
                        target=self._stream_reader,
                        args=(self.process.stdout, self.config.stdout_handler, False),
                        daemon=True
                    )
                    self._stdout_reader.start()
                
                if not stderr_file:
                    self._stderr_reader = Thread(
                        target=self._stream_reader,
                        args=(self.process.stderr, self.config.stderr_handler, True),
                        daemon=True
                    )
                    self._stderr_reader.start()
                
                # Wait for server to be ready
                ready = await self._wait_for_ready()
                
                if ready:
                    self.status = ServerStatus.RUNNING
                    logger.info(f"Server {self.config.name} started successfully (PID: {self.process.pid})")
                    
                    # Post-start hook
                    if self.config.post_start_hook:
                        try:
                            self.config.post_start_hook()
                        except Exception as e:
                            logger.error(f"Post-start hook failed for {self.config.name}: {e}")
                    
                    # Start health monitoring
                    self._health_check_task = asyncio.create_task(self._health_monitor())
                    
                    return True
                else:
                    logger.error(f"Server {self.config.name} failed to become ready")
                    await self.stop()
                    self.status = ServerStatus.FAILED
                    return False
                    
            except Exception as e:
                logger.error(f"Failed to start server {self.config.name}: {e}")
                self.status = ServerStatus.FAILED
                if stdout_file:
                    stdout_file.close()
                if stderr_file:
                    stderr_file.close()
                return False
    
    async def stop(self, force: bool = False) -> bool:
        """Stop the server process"""
        with self._lock:
            if self.status == ServerStatus.STOPPED:
                return True
            
            self.status = ServerStatus.STOPPING
            logger.info(f"Stopping server: {self.config.name}")
            
            # Pre-stop hook
            if self.config.pre_stop_hook:
                try:
                    self.config.pre_stop_hook()
                except Exception as e:
                    logger.error(f"Pre-stop hook failed for {self.config.name}: {e}")
            
            # Cancel health monitoring
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
            
            # Signal readers to stop
            self._stop_event.set()
            
            if self.process:
                try:
                    if force:
                        # Force kill
                        if sys.platform == 'win32':
                            self.process.kill()
                        else:
                            os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    else:
                        # Graceful shutdown
                        if sys.platform == 'win32':
                            self.process.terminate()
                        else:
                            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                        
                        # Wait for shutdown
                        try:
                            await asyncio.wait_for(
                                asyncio.create_task(self._wait_for_exit()),
                                timeout=self.config.shutdown_timeout
                            )
                        except asyncio.TimeoutError:
                            logger.warning(f"Server {self.config.name} did not stop gracefully, forcing...")
                            if sys.platform == 'win32':
                                self.process.kill()
                            else:
                                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                            await self._wait_for_exit()
                    
                    self.process = None
                    
                except Exception as e:
                    logger.error(f"Error stopping server {self.config.name}: {e}")
                    return False
            
            # Update metrics
            if self.metrics.start_time:
                self.metrics.stop_time = datetime.now()
                self.metrics.total_uptime += self.metrics.stop_time - self.metrics.start_time
            
            self.status = ServerStatus.STOPPED
            logger.info(f"Server {self.config.name} stopped")
            
            # Post-stop hook
            if self.config.post_stop_hook:
                try:
                    self.config.post_stop_hook()
                except Exception as e:
                    logger.error(f"Post-stop hook failed for {self.config.name}: {e}")
            
            return True
    
    async def restart(self) -> bool:
        """Restart the server"""
        logger.info(f"Restarting server: {self.config.name}")
        await self.stop()
        await asyncio.sleep(self.config.restart_delay)
        success = await self.start()
        if success:
            self.metrics.restart_count += 1
        return success
    
    async def _wait_for_ready(self) -> bool:
        """Wait for server to be ready"""
        start_time = time.time()
        
        while time.time() - start_time < self.config.startup_timeout:
            # Check if process is still running
            if self.process and self.process.poll() is not None:
                logger.error(f"Server {self.config.name} exited during startup")
                return False
            
            # Perform health check
            if await self._health_checker.check(self.config):
                return True
            
            await asyncio.sleep(0.5)
        
        return False
    
    async def _wait_for_exit(self):
        """Wait for process to exit"""
        while self.process and self.process.poll() is None:
            await asyncio.sleep(0.1)
    
    async def _health_monitor(self):
        """Monitor server health"""
        consecutive_failures = 0
        
        while self.status == ServerStatus.RUNNING:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                
                # Update process metrics
                if self.process:
                    try:
                        proc = psutil.Process(self.process.pid)
                        self.metrics.cpu_usage = proc.cpu_percent(interval=0.1)
                        self.metrics.memory_usage = proc.memory_info().rss / 1024 / 1024  # MB
                    except psutil.NoSuchProcess:
                        pass
                
                # Perform health check
                healthy = await self._health_checker.check(self.config)
                self.metrics.last_health_check = datetime.now()
                
                if healthy:
                    consecutive_failures = 0
                    if self.status == ServerStatus.UNHEALTHY:
                        self.status = ServerStatus.RUNNING
                        logger.info(f"Server {self.config.name} is healthy again")
                else:
                    consecutive_failures += 1
                    self.metrics.health_check_failures += 1
                    
                    if consecutive_failures >= 3:
                        self.status = ServerStatus.UNHEALTHY
                        logger.warning(f"Server {self.config.name} is unhealthy")
                        
                        # Auto-restart if within limits
                        if self.metrics.restart_count < self.config.max_restarts:
                            logger.info(f"Auto-restarting unhealthy server {self.config.name}")
                            await self.restart()
                            break
                        else:
                            logger.error(f"Server {self.config.name} exceeded max restarts")
                            self.status = ServerStatus.FAILED
                            break
                            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitor for {self.config.name}: {e}")
    
    def is_running(self) -> bool:
        """Check if server is running"""
        return self.status in (ServerStatus.RUNNING, ServerStatus.UNHEALTHY)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get server metrics"""
        return {
            'name': self.config.name,
            'status': self.status.value,
            'pid': self.process.pid if self.process else None,
            'metrics': self.metrics.to_dict()
        }


class ServerManager:
    """Manages multiple server processes"""
    
    def __init__(self):
        self.servers: Dict[str, ManagedServer] = {}
        self._executor = ThreadPoolExecutor(max_workers=10)
        self._lock = asyncio.Lock()
    
    async def add_server(self, config: ServerConfig) -> None:
        """Add a server to be managed"""
        async with self._lock:
            if config.name in self.servers:
                raise ValueError(f"Server {config.name} already exists")
            self.servers[config.name] = ManagedServer(config)
            logger.info(f"Added server: {config.name}")
    
    async def remove_server(self, name: str, force: bool = False) -> bool:
        """Remove a server from management"""
        async with self._lock:
            if name not in self.servers:
                return False
            
            server = self.servers[name]
            if server.is_running():
                await server.stop(force=force)
            
            del self.servers[name]
            logger.info(f"Removed server: {name}")
            return True
    
    async def start_server(self, name: str) -> bool:
        """Start a specific server"""
        if name not in self.servers:
            logger.error(f"Server {name} not found")
            return False
        return await self.servers[name].start()
    
    async def stop_server(self, name: str, force: bool = False) -> bool:
        """Stop a specific server"""
        if name not in self.servers:
            logger.error(f"Server {name} not found")
            return False
        return await self.servers[name].stop(force=force)
    
    async def restart_server(self, name: str) -> bool:
        """Restart a specific server"""
        if name not in self.servers:
            logger.error(f"Server {name} not found")
            return False
        return await self.servers[name].restart()
    
    async def start_all(self) -> Dict[str, bool]:
        """Start all servers"""
        results = {}
        tasks = []
        
        for name, server in self.servers.items():
            task = asyncio.create_task(server.start())
            tasks.append((name, task))
        
        for name, task in tasks:
            results[name] = await task
        
        return results
    
    async def stop_all(self, force: bool = False) -> Dict[str, bool]:
        """Stop all servers"""
        results = {}
        tasks = []
        
        for name, server in self.servers.items():
            task = asyncio.create_task(server.stop(force=force))
            tasks.append((name, task))
        
        for name, task in tasks:
            results[name] = await task
        
        return results
    
    def get_status(self, name: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get status of one or all servers"""
        if name:
            if name not in self.servers:
                return {"error": f"Server {name} not found"}
            return self.servers[name].get_metrics()
        else:
            return [server.get_metrics() for server in self.servers.values()]
    
    def is_healthy(self, name: Optional[str] = None) -> bool:
        """Check if server(s) are healthy"""
        if name:
            if name not in self.servers:
                return False
            return self.servers[name].status == ServerStatus.RUNNING
        else:
            return all(
                server.status == ServerStatus.RUNNING 
                for server in self.servers.values()
            )
    
    async def wait_for_all_ready(self, timeout: float = 60.0) -> bool:
        """Wait for all servers to be ready"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if all(server.status == ServerStatus.RUNNING for server in self.servers.values()):
                return True
            await asyncio.sleep(1)
        
        return False
    
    @contextmanager
    def managed_servers(self, configs: List[ServerConfig]):
        """Context manager for managing servers"""
        async def setup():
            for config in configs:
                await self.add_server(config)
            await self.start_all()
            await self.wait_for_all_ready()
        
        async def teardown():
            await self.stop_all()
        
        # Run setup
        asyncio.run(setup())
        
        try:
            yield self
        finally:
            # Run teardown
            asyncio.run(teardown())
    
    async def cleanup(self):
        """Clean up resources"""
        await self.stop_all(force=True)
        self._executor.shutdown(wait=True)


# Example usage and testing utilities
class TSMServerPresets:
    """Preset configurations for TSM servers"""
    
    @staticmethod
    def grpc_server(name: str = "tsm-grpc", port: int = 50051) -> ServerConfig:
        """TSM gRPC server configuration"""
        return ServerConfig(
            name=name,
            command=["python", "-m", "mock_server.server"],
            port=port,
            health_check_type=HealthCheckType.GRPC,
            startup_timeout=30.0,
            env_vars={"TSM_SERVER_PORT": str(port)}
        )
    
    @staticmethod
    def homomorphic_server(name: str = "tsm-homomorphic", port: int = 50052) -> ServerConfig:
        """Homomorphic search server configuration"""
        return ServerConfig(
            name=name,
            command=["python", "-m", "homomorphic_server"],
            port=port,
            health_check_type=HealthCheckType.TCP,
            startup_timeout=45.0,  # Longer startup for key generation
            env_vars={"HE_SERVER_PORT": str(port)}
        )
    
    @staticmethod
    def ai_security_server(name: str = "tsm-ai", port: int = 50053) -> ServerConfig:
        """AI security analysis server configuration"""
        return ServerConfig(
            name=name,
            command=["python", "-m", "ai_security_server"],
            port=port,
            health_check_type=HealthCheckType.TCP,
            startup_timeout=60.0,  # Longer startup for model loading
            env_vars={"AI_SERVER_PORT": str(port)}
        )


async def example_usage():
    """Example usage of ServerManager"""
    # Create manager
    manager = ServerManager()
    
    # Add servers
    await manager.add_server(TSMServerPresets.grpc_server())
    await manager.add_server(TSMServerPresets.homomorphic_server())
    
    # Start all servers
    logger.info("Starting all servers...")
    results = await manager.start_all()
    for name, success in results.items():
        logger.info(f"  {name}: {'Started' if success else 'Failed'}")
    
    # Wait for all to be ready
    if await manager.wait_for_all_ready():
        logger.info("All servers are ready!")
    
    # Check status
    status = manager.get_status()
    logger.info(f"Server status: {json.dumps(status, indent=2)}")
    
    # Let them run for a bit
    await asyncio.sleep(10)
    
    # Stop all servers
    logger.info("Stopping all servers...")
    await manager.stop_all()
    
    # Cleanup
    await manager.cleanup()


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
