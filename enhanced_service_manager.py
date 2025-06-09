#!/usr/bin/env python3
"""
Enhanced service manager with persistence and health monitoring
Replaces start_all_services.py with better reliability
"""

import subprocess
import time
import requests
import threading
import signal
import sys
import os
from datetime import datetime

class ServiceManager:
    def __init__(self):
        self.services = {
            'data-acquisition': {'port': 8001, 'path': 'services/data-acquisition', 'process': None},
            'technical-analysis': {'port': 8002, 'path': 'services/technical-analysis', 'process': None},
            'ml-service': {'port': 8003, 'path': 'services/ml-service', 'process': None},
            'strategy-engine': {'port': 8004, 'path': 'services/strategy-engine', 'process': None},
            'risk-management': {'port': 8005, 'path': 'services/risk-management', 'process': None},
            'options-analytics': {'port': 8006, 'path': 'services/options-analytics', 'process': None}
        }
        self.running = True
        self.health_check_interval = 30  # seconds
        self.restart_delay = 5  # seconds
        
    def log(self, message):
        """Enhanced logging with timestamps"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
        # Also log to file
        with open("service_manager.log", "a") as f:
            f.write(f"[{timestamp}] {message}\n")

    def start_service(self, service_name):
        """Start a single service with enhanced error handling"""
        service = self.services[service_name]
        service_path = service['path']
        port = service['port']
        
        try:
            # Change to service directory
            original_dir = os.getcwd()
            os.chdir(service_path)
            
            # Start the service with keep-alive settings
            cmd = [
                sys.executable, 
                "main.py",
                "--host", "0.0.0.0",
                "--port", str(port),
                "--workers", "1",
                "--timeout-keep-alive", "300",  # 5 minutes keep-alive
                "--timeout-graceful-shutdown", "30"
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            service['process'] = process
            os.chdir(original_dir)
            
            self.log(f"Started {service_name} on port {port} (PID: {process.pid})")
            return True
            
        except Exception as e:
            self.log(f"Failed to start {service_name}: {e}")
            os.chdir(original_dir)
            return False

    def check_service_health(self, service_name):
        """Check if service is responding to health checks"""
        service = self.services[service_name]
        port = service['port']
        
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def restart_service(self, service_name):
        """Restart a failed service"""
        self.log(f"Restarting {service_name}...")
        
        # Stop the service if it's running
        service = self.services[service_name]
        if service['process']:
            try:
                service['process'].terminate()
                service['process'].wait(timeout=10)
            except:
                service['process'].kill()
            service['process'] = None
        
        # Wait before restart
        time.sleep(self.restart_delay)
        
        # Start the service
        return self.start_service(service_name)

    def start_all_services(self):
        """Start all services"""
        self.log("Starting all services...")
        
        for service_name in self.services:
            if not self.start_service(service_name):
                self.log(f"Failed to start {service_name}")
                return False
            time.sleep(2)  # Stagger startup
        
        self.log("All services started successfully")
        return True

    def health_monitor(self):
        """Continuous health monitoring with auto-restart"""
        while self.running:
            try:
                for service_name in self.services:
                    service = self.services[service_name]
                    
                    # Check if process is still running
                    if service['process'] and service['process'].poll() is not None:
                        self.log(f"Process for {service_name} has died (exit code: {service['process'].returncode})")
                        self.restart_service(service_name)
                        continue
                    
                    # Check if service is responding
                    if not self.check_service_health(service_name):
                        self.log(f"Health check failed for {service_name}")
                        self.restart_service(service_name)
                    else:
                        # Service is healthy - log occasionally
                        if int(time.time()) % 300 == 0:  # Every 5 minutes
                            self.log(f"{service_name} is healthy")
                
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                self.log(f"Error in health monitor: {e}")
                time.sleep(10)

    def stop_all_services(self):
        """Gracefully stop all services"""
        self.running = False
        self.log("Stopping all services...")
        
        for service_name, service in self.services.items():
            if service['process']:
                try:
                    self.log(f"Stopping {service_name}...")
                    service['process'].terminate()
                    service['process'].wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.log(f"Force killing {service_name}...")
                    service['process'].kill()
                except Exception as e:
                    self.log(f"Error stopping {service_name}: {e}")
        
        self.log("All services stopped")

    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.log("Received shutdown signal")
        self.stop_all_services()
        sys.exit(0)

    def run(self):
        """Main execution loop"""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Start all services
        if not self.start_all_services():
            self.log("Failed to start services")
            return False
        
        # Wait for services to be ready
        self.log("Waiting for services to be ready...")
        time.sleep(10)
        
        # Verify all services are healthy
        all_healthy = True
        for service_name in self.services:
            if not self.check_service_health(service_name):
                self.log(f"Service {service_name} failed initial health check")
                all_healthy = False
        
        if not all_healthy:
            self.log("Some services failed initial health check")
            return False
        
        self.log("All services are healthy and ready")
        
        # Start health monitoring in background
        monitor_thread = threading.Thread(target=self.health_monitor, daemon=True)
        monitor_thread.start()
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)

def main():
    """Main entry point"""
    print("=== AI Options Trading - Enhanced Service Manager ===")
    print("Starting persistent service management...")
    
    manager = ServiceManager()
    manager.run()

if __name__ == "__main__":
    main()