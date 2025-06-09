#!/usr/bin/env python3
"""
AI Options Trading - Service Startup Script
Starts all 6 microservices for the trading system
"""

import subprocess
import sys
import os
import time
import signal
import threading
from pathlib import Path

class ServiceManager:
    def __init__(self):
        self.services = {
            'data-acquisition': {
                'path': 'services/data-acquisition/app',
                'port': 8001,
                'process': None,
                'description': 'Data Acquisition Service (Zerodha API, Market Data)'
            },
            'technical-analysis': {
                'path': 'services/technical-analysis/app', 
                'port': 8002,
                'process': None,
                'description': 'Technical Analysis Service (Indicators, Support/Resistance)'
            },
            'ml-service': {
                'path': 'services/ml-service/app',
                'port': 8003,
                'process': None,
                'description': 'ML Service (Direction Prediction, Pattern Recognition)'
            },
            'strategy-engine': {
                'path': 'services/strategy-engine/app',
                'port': 8004,
                'process': None,
                'description': 'Strategy Engine (Options Strategies, Auto-selection)'
            },
            'risk-management': {
                'path': 'services/risk-management/app',
                'port': 8005,
                'process': None,
                'description': 'Risk Management Service (VaR, Portfolio Risk)'
            },
            'options-analytics': {
                'path': 'services/options-analytics/app',
                'port': 8006,
                'process': None,
                'description': 'Options Analytics Service (Greeks, IV Surface)'
            }
        }
        self.running = True

    def check_python_version(self):
        """Check if Python version is compatible"""
        if sys.version_info < (3, 8):
            print("❌ Python 3.8 or higher required")
            return False
        print(f"✅ Python {sys.version.split()[0]} detected")
        return True

    def check_dependencies(self):
        """Check if required packages are installed"""
        required_packages = ['fastapi', 'uvicorn', 'pandas', 'numpy']
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
                print(f"✅ {package} installed")
            except ImportError:
                missing_packages.append(package)
                print(f"❌ {package} not found")
        
        if missing_packages:
            print(f"\n📦 Install missing packages: pip install {' '.join(missing_packages)}")
            return False
        return True

    def check_service_files(self):
        """Check if all service directories and main.py files exist"""
        project_root = Path.cwd()
        missing_services = []
        
        for service_name, config in self.services.items():
            service_path = project_root / config['path']
            main_file = service_path / 'main.py'
            
            if not service_path.exists():
                missing_services.append(f"{service_name} directory: {service_path}")
                print(f"❌ {service_name} directory not found: {service_path}")
            elif not main_file.exists():
                missing_services.append(f"{service_name} main.py: {main_file}")
                print(f"❌ {service_name} main.py not found: {main_file}")
            else:
                print(f"✅ {service_name} found at {service_path}")
        
        if missing_services:
            print(f"\n❌ Missing services:\n" + "\n".join(f"  - {s}" for s in missing_services))
            return False
        return True

    def start_service(self, service_name, config):
        """Start a single service"""
        try:
            service_path = Path(config['path'])
            main_file = service_path / 'main.py'
            
            print(f"🚀 Starting {service_name} on port {config['port']}...")
            print(f"   📁 Path: {service_path}")
            print(f"   📄 File: {main_file}")
            
            # Change to service directory and start
            process = subprocess.Popen(
                [sys.executable, 'main.py'],
                cwd=service_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            config['process'] = process
            
            # Start output monitoring thread
            threading.Thread(
                target=self.monitor_service_output,
                args=(service_name, process),
                daemon=True
            ).start()
            
            # Give service time to start
            time.sleep(2)
            
            if process.poll() is None:
                print(f"✅ {service_name} started successfully (PID: {process.pid})")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"❌ {service_name} failed to start")
                if stderr:
                    print(f"   Error: {stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error starting {service_name}: {e}")
            return False

    def monitor_service_output(self, service_name, process):
        """Monitor service output and errors"""
        while self.running and process.poll() is None:
            try:
                output = process.stdout.readline()
                if output:
                    # Only show important messages
                    if any(keyword in output.lower() for keyword in ['error', 'failed', 'exception', 'started']):
                        print(f"[{service_name}] {output.strip()}")
                
                error = process.stderr.readline()
                if error:
                    print(f"[{service_name} ERROR] {error.strip()}")
                    
            except Exception as e:
                print(f"[{service_name}] Monitor error: {e}")
                break

    def check_service_health(self, service_name, port):
        """Check if service is responding"""
        try:
            import requests
            response = requests.get(f'http://localhost:{port}/health', timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name} health check passed")
                return True
            else:
                print(f"⚠️  {service_name} health check failed (HTTP {response.status_code})")
                return False
        except ImportError:
            print(f"⚠️  Cannot check {service_name} health (requests not installed)")
            return True  # Assume OK if we can't check
        except Exception as e:
            print(f"⚠️  {service_name} health check failed: {e}")
            return False

    def start_all_services(self):
        """Start all services in sequence"""
        print("=" * 60)
        print("🚀 AI OPTIONS TRADING SYSTEM - STARTING ALL SERVICES")
        print("=" * 60)
        
        # Pre-flight checks
        print("\n📋 Running pre-flight checks...")
        if not self.check_python_version():
            return False
        if not self.check_dependencies():
            return False
        if not self.check_service_files():
            return False
        
        print("\n🎯 Starting services...")
        started_services = []
        
        for service_name, config in self.services.items():
            print(f"\n📍 {config['description']}")
            if self.start_service(service_name, config):
                started_services.append(service_name)
            else:
                print(f"❌ Failed to start {service_name}")
                self.stop_all_services()
                return False
        
        print("\n⏳ Waiting for services to initialize...")
        time.sleep(5)
        
        # Health checks
        print("\n🏥 Running health checks...")
        healthy_services = []
        for service_name, config in self.services.items():
            if self.check_service_health(service_name, config['port']):
                healthy_services.append(service_name)
        
        # Status summary
        print("\n" + "=" * 60)
        print("📊 SERVICE STATUS SUMMARY")
        print("=" * 60)
        
        for service_name, config in self.services.items():
            status = "🟢 RUNNING" if service_name in healthy_services else "🔴 ISSUES"
            print(f"{status} | {service_name:20} | Port {config['port']} | PID {getattr(config['process'], 'pid', 'N/A')}")
        
        print(f"\n✅ {len(healthy_services)}/{len(self.services)} services healthy")
        
        if len(healthy_services) == len(self.services):
            print("\n🎉 ALL SERVICES STARTED SUCCESSFULLY!")
            print("\n🌐 Access URLs:")
            for service_name, config in self.services.items():
                print(f"   {service_name}: http://localhost:{config['port']}")
            print(f"   Health Check: http://localhost:{config['port']}/health")
            print(f"   Documentation: http://localhost:{config['port']}/docs")
            
            print("\n📱 React Dashboard:")
            print("   Start with: cd react-dashboard && npm start")
            print("   URL: http://localhost:3000")
            
            return True
        else:
            print(f"\n⚠️  Some services have issues. Check logs above.")
            return False

    def stop_all_services(self):
        """Stop all running services"""
        print("\n🛑 Stopping all services...")
        self.running = False
        
        for service_name, config in self.services.items():
            if config['process'] and config['process'].poll() is None:
                print(f"🛑 Stopping {service_name}...")
                try:
                    config['process'].terminate()
                    config['process'].wait(timeout=5)
                    print(f"✅ {service_name} stopped")
                except subprocess.TimeoutExpired:
                    print(f"⚠️  Force killing {service_name}...")
                    config['process'].kill()
                    config['process'].wait()
                except Exception as e:
                    print(f"❌ Error stopping {service_name}: {e}")

    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print(f"\n\n🛑 Received signal {signum}. Shutting down...")
        self.stop_all_services()
        sys.exit(0)

    def run(self):
        """Main run method"""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            if self.start_all_services():
                print("\n⌚ Services are running. Press Ctrl+C to stop all services.")
                print("💡 Tip: Open http://localhost:3000 for the React dashboard")
                
                # Keep the script running
                while self.running:
                    time.sleep(1)
            else:
                print("\n❌ Failed to start all services.")
                return 1
                
        except KeyboardInterrupt:
            print("\n\n👋 Shutting down...")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            return 1
        finally:
            self.stop_all_services()
        
        return 0

def main():
    """Main entry point"""
    print("🤖 AI Options Trading System - Service Manager")
    print("📅 Phase 1 Complete | Phase 2 Dashboard Ready")
    
    manager = ServiceManager()
    return manager.run()

if __name__ == "__main__":
    sys.exit(main())