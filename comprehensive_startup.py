#!/usr/bin/env python3
"""
Comprehensive Service Startup Script
Based on your repository structure: https://github.com/project2024-25/ai-options-trading
"""

import subprocess
import time
import requests
import os
import sys
from pathlib import Path
from datetime import datetime

class ServiceManager:
    def __init__(self):
        self.project_root = Path.cwd()
        self.services = {
            8001: {"name": "data-acquisition", "display": "Data Acquisition", "process": None},
            8002: {"name": "technical-analysis", "display": "Technical Analysis", "process": None},
            8003: {"name": "ml-service", "display": "ML Service", "process": None},
            8004: {"name": "strategy-engine", "display": "Strategy Engine", "process": None},
            8005: {"name": "risk-management", "display": "Risk Management", "process": None},
            8006: {"name": "options-analytics", "display": "Options Analytics", "process": None},
            8007: {"name": "order-execution", "display": "Order Execution", "process": None}
        }
        
    def check_infrastructure(self):
        """Check and start infrastructure services"""
        print("🔧 CHECKING INFRASTRUCTURE")
        print("=" * 40)
        
        # Check if Docker is running
        try:
            result = subprocess.run(["docker", "ps"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ Docker is running")
            else:
                print("❌ Docker is not running - please start Docker Desktop")
                return False
        except:
            print("❌ Docker is not available - please install Docker")
            return False
        
        # Start infrastructure services
        print("\n🚀 Starting infrastructure services...")
        try:
            # Stop any existing containers
            subprocess.run(["docker-compose", "down"], capture_output=True)
            
            # Start infrastructure
            result = subprocess.run(["docker-compose", "up", "-d"], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Infrastructure services started")
                print("   - PostgreSQL (TimescaleDB)")
                print("   - Redis")
                print("   - N8N (already running)")
            else:
                print(f"⚠️ Infrastructure startup issues: {result.stderr}")
        except Exception as e:
            print(f"❌ Failed to start infrastructure: {e}")
            return False
        
        # Wait for infrastructure to be ready
        print("\n⏳ Waiting for infrastructure to be ready...")
        time.sleep(15)
        
        # Test infrastructure connectivity
        infra_ready = True
        
        # Test PostgreSQL
        try:
            import asyncio
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            
            # Simple TCP test for PostgreSQL
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('localhost', 5432))
            sock.close()
            
            if result == 0:
                print("✅ PostgreSQL: Ready")
            else:
                print("⚠️ PostgreSQL: Not yet ready")
                infra_ready = False
        except:
            print("⚠️ PostgreSQL: Connection test failed")
            infra_ready = False
        
        # Test Redis
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('localhost', 6379))
            sock.close()
            
            if result == 0:
                print("✅ Redis: Ready")
            else:
                print("⚠️ Redis: Not yet ready")
        except:
            print("⚠️ Redis: Connection test failed")
        
        # Test N8N
        try:
            response = requests.get("http://localhost:5678/healthz", timeout=5)
            if response.status_code == 200:
                print("✅ N8N: Ready")
            else:
                print("⚠️ N8N: Not responding properly")
        except:
            print("⚠️ N8N: Connection failed")
        
        return infra_ready
    
    def start_service(self, port, service_info):
        """Start a single service"""
        service_name = service_info["name"]
        display_name = service_info["display"]
        
        service_path = self.project_root / "services" / service_name / "app"
        main_file = service_path / "main.py"
        
        if not main_file.exists():
            print(f"❌ {display_name}: main.py not found at {main_file}")
            return None
        
        try:
            # Set environment variables
            env = os.environ.copy()
            env["PYTHONPATH"] = str(self.project_root)
            
            # Start the service
            process = subprocess.Popen(
                [sys.executable, "main.py"],
                cwd=str(service_path),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print(f"🚀 {display_name}: Started (PID: {process.pid})")
            return process
            
        except Exception as e:
            print(f"❌ {display_name}: Failed to start - {e}")
            return None
    
    def wait_for_service_ready(self, port, display_name, timeout=60):
        """Wait for service to be ready"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=5)
                if response.status_code == 200:
                    elapsed = time.time() - start_time
                    print(f"✅ {display_name}: Ready in {elapsed:.1f}s")
                    return True
            except:
                pass
            
            print(f"⏳ {display_name}: Waiting...")
            time.sleep(3)
        
        print(f"❌ {display_name}: Timeout after {timeout}s")
        return False
    
    def start_all_services(self):
        """Start all services in order"""
        print("🚀 STARTING ALL PYTHON SERVICES")
        print("=" * 40)
        
        # Start services
        for port, service_info in self.services.items():
            process = self.start_service(port, service_info)
            service_info["process"] = process
            time.sleep(2)  # Stagger startup
        
        print("\n⏳ Waiting for services to initialize...")
        time.sleep(10)
        
        # Check service readiness
        ready_services = 0
        for port, service_info in self.services.items():
            if service_info["process"] and service_info["process"].poll() is None:
                if self.wait_for_service_ready(port, service_info["display"], timeout=30):
                    ready_services += 1
                else:
                    print(f"⚠️ {service_info['display']}: Service started but not responding to health checks")
            else:
                print(f"❌ {service_info['display']}: Process not running")
        
        return ready_services
    
    def test_all_endpoints(self):
        """Test key endpoints for each service"""
        print("\n🧪 TESTING SERVICE ENDPOINTS")
        print("=" * 40)
        
        endpoint_tests = {
            8001: ["/health", "/api/data/nifty-snapshot"],
            8002: ["/health", "/api/analysis/indicators/NIFTY"],
            8003: ["/health", "/api/ml/direction-prediction/NIFTY"],
            8004: ["/health", "/api/strategy/signals/NIFTY"],
            8005: ["/health", "/api/risk/position-sizing"],
            8006: ["/health", "/api/options/greeks/NIFTY"],
            8007: ["/health"]  # Order execution
        }
        
        total_tests = 0
        passed_tests = 0
        
        for port, endpoints in endpoint_tests.items():
            service_name = self.services[port]["display"]
            print(f"\n{service_name}:")
            
            for endpoint in endpoints:
                total_tests += 1
                try:
                    url = f"http://localhost:{port}{endpoint}"
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        print(f"  ✅ {endpoint}")
                        passed_tests += 1
                    else:
                        print(f"  ❌ {endpoint} (HTTP {response.status_code})")
                except Exception as e:
                    print(f"  ❌ {endpoint} (Error: {str(e)[:30]})")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"\n📊 Endpoint Tests: {passed_tests}/{total_tests} ({success_rate:.1f}% success)")
        
        return success_rate
    
    def generate_status_report(self):
        """Generate comprehensive status report"""
        print("\n📋 SYSTEM STATUS REPORT")
        print("=" * 50)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Service status
        print("SERVICES:")
        running_services = 0
        for port, service_info in self.services.items():
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    uptime = data.get('uptime_seconds', 0)
                    print(f"  ✅ {service_info['display']:20} | {status:8} | {uptime:.0f}s uptime")
                    running_services += 1
                else:
                    print(f"  ❌ {service_info['display']:20} | HTTP {response.status_code}")
            except:
                print(f"  ❌ {service_info['display']:20} | NOT RESPONDING")
        
        print()
        print("INFRASTRUCTURE:")
        
        # Check N8N
        try:
            response = requests.get("http://localhost:5678/healthz", timeout=5)
            print(f"  ✅ N8N                   | {'HEALTHY' if response.status_code == 200 else 'DEGRADED'}")
        except:
            print(f"  ❌ N8N                   | NOT ACCESSIBLE")
        
        # Check Docker containers
        try:
            result = subprocess.run(["docker", "ps", "--format", "table {{.Names}}\\t{{.Status}}"], 
                                  capture_output=True, text=True)
            if "postgres" in result.stdout:
                print("  ✅ PostgreSQL            | RUNNING")
            if "redis" in result.stdout:
                print("  ✅ Redis                 | RUNNING")
        except:
            print("  ⚠️ Docker containers     | CHECK MANUALLY")
        
        print()
        print("SUMMARY:")
        print(f"  Running Services: {running_services}/7")
        
        if running_services >= 6:
            print("  🎉 STATUS: EXCELLENT - System fully operational")
            status = "excellent"
        elif running_services >= 4:
            print("  ✅ STATUS: GOOD - Most services running")
            status = "good"
        elif running_services >= 2:
            print("  ⚠️ STATUS: PARTIAL - Several services need attention")
            status = "partial"
        else:
            print("  ❌ STATUS: CRITICAL - System needs troubleshooting")
            status = "critical"
        
        return status, running_services
    
    def cleanup_on_exit(self):
        """Clean up processes on exit"""
        print("\n🧹 Cleaning up processes...")
        for port, service_info in self.services.items():
            if service_info["process"]:
                try:
                    service_info["process"].terminate()
                    print(f"  ✅ Stopped {service_info['display']}")
                except:
                    pass

def main():
    """Main startup function"""
    manager = ServiceManager()
    
    print("🚀 AI OPTIONS TRADING SYSTEM - COMPREHENSIVE STARTUP")
    print("=" * 60)
    print(f"Project Root: {manager.project_root}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Step 1: Check and start infrastructure
        print("STEP 1: Infrastructure Check")
        if not manager.check_infrastructure():
            print("❌ Infrastructure setup failed. Please fix and retry.")
            return False
        
        print("\nSTEP 2: Start Python Services")
        ready_services = manager.start_all_services()
        
        print("\nSTEP 3: Test Endpoints")
        endpoint_success = manager.test_all_endpoints()
        
        print("\nSTEP 4: Final Status Report")
        status, running_count = manager.generate_status_report()
        
        # Final recommendations
        print("\n🎯 NEXT STEPS:")
        print("-" * 20)
        
        if status == "excellent":
            print("✅ System is ready for live data integration!")
            print("   Run: python live_data_integration.py")
        elif status == "good":
            print("✅ System is mostly ready")
            print("   Fix any failed services, then proceed with integration")
        else:
            print("⚠️ System needs attention")
            print("   Check service logs and restart failed services")
            print("   Re-run this script after fixes")
        
        print(f"\n📊 SUCCESS METRICS:")
        print(f"   Services Running: {running_count}/7")
        print(f"   Endpoint Success: {endpoint_success:.1f}%")
        
        return status in ["excellent", "good"]
        
    except KeyboardInterrupt:
        print("\n⏹️ Startup interrupted by user")
        manager.cleanup_on_exit()
        return False
    except Exception as e:
        print(f"\n❌ Startup failed: {e}")
        manager.cleanup_on_exit()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Startup completed successfully!")
        print("   Services are running in the background")
        print("   Press Ctrl+C to stop all services when done")
        
        try:
            # Keep script running to maintain services
            while True:
                time.sleep(30)
                # Quick health check every 30 seconds
                print(".", end="", flush=True)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down all services...")
    else:
        print("\n❌ Startup failed - check logs and retry")
    
    sys.exit(0 if success else 1)