#!/usr/bin/env python3
"""
AI Options Trading System - Simple Health Monitor (Windows Compatible)
No emojis - works on all Windows systems
"""

import requests
import time
from datetime import datetime

class SimpleSystemMonitor:
    def __init__(self):
        self.services = {
            'Data Acquisition': 8001,
            'Technical Analysis': 8002,
            'ML Service': 8003,
            'Strategy Engine': 8004,
            'Risk Management': 8005,
            'Options Analytics': 8006,
            'Order Execution': 8007
        }
        self.n8n_url = "http://localhost:5678"
        
    def check_service_health(self, name, port):
        """Check individual service health"""
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                
                if status == 'healthy':
                    print(f"[OK] {name} (:{port}) - {status.upper()}")
                    return True, status
                else:
                    print(f"[WARN] {name} (:{port}) - {status.upper()}")
                    return True, status
            else:
                print(f"[ERROR] {name} (:{port}) - HTTP {response.status_code}")
                return False, f"HTTP {response.status_code}"
        except requests.exceptions.ConnectionError:
            print(f"[ERROR] {name} (:{port}) - CONNECTION REFUSED (Service not running)")
            return False, "NOT_RUNNING"
        except requests.exceptions.Timeout:
            print(f"[ERROR] {name} (:{port}) - TIMEOUT (Service starting or overloaded)")
            return False, "TIMEOUT"
        except Exception as e:
            print(f"[ERROR] {name} (:{port}) - ERROR: {str(e)}")
            return False, str(e)
    
    def check_n8n_health(self):
        """Check N8N service health"""
        try:
            response = requests.get(self.n8n_url, timeout=10)
            if response.status_code == 200:
                print("[OK] N8N - HEALTHY (Web interface accessible)")
                return True, "HEALTHY"
            else:
                print(f"[ERROR] N8N - HTTP {response.status_code}")
                return False, f"HTTP {response.status_code}"
        except requests.exceptions.ConnectionError:
            print("[ERROR] N8N - CONNECTION REFUSED (Service not running)")
            return False, "NOT_RUNNING"
        except Exception as e:
            print(f"[ERROR] N8N - ERROR: {str(e)}")
            return False, str(e)
    
    def quick_check(self):
        """Quick health check without detailed output"""
        try:
            healthy_services = 0
            total_services = len(self.services) + 1  # +1 for N8N
            
            print("\n" + "="*60)
            print("AI OPTIONS TRADING SYSTEM - QUICK HEALTH CHECK")
            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*60)
            
            # Check Python services
            print("\nPYTHON SERVICES:")
            print("-" * 40)
            for name, port in self.services.items():
                try:
                    response = requests.get(f"http://localhost:{port}/health", timeout=8)
                    if response.status_code == 200:
                        print(f"[OK] {name}")
                        healthy_services += 1
                    else:
                        print(f"[ERROR] {name} - HTTP {response.status_code}")
                except requests.exceptions.Timeout:
                    print(f"[WARN] {name} - STARTING (timeout - give it more time)")
                except requests.exceptions.ConnectionError:
                    print(f"[ERROR] {name} - NOT RUNNING")
                except Exception as e:
                    print(f"[ERROR] {name} - {str(e)[:50]}")
            
            # Check N8N
            print("\nWORKFLOW ENGINE:")
            print("-" * 40)
            try:
                response = requests.get(self.n8n_url, timeout=5)
                if response.status_code == 200:
                    print("[OK] N8N - HEALTHY")
                    healthy_services += 1
                else:
                    print(f"[ERROR] N8N - HTTP {response.status_code}")
            except:
                print("[ERROR] N8N - NOT ACCESSIBLE")
            
            # Summary
            print("\n" + "="*60)
            health_percentage = (healthy_services / total_services) * 100
            print(f"SYSTEM HEALTH: {healthy_services}/{total_services} services ({health_percentage:.1f}%)")
            
            if health_percentage >= 85:
                print("STATUS: GOOD - System ready for trading")
            elif health_percentage >= 50:
                print("STATUS: DEGRADED - Some services need attention")
            else:
                print("STATUS: CRITICAL - System needs troubleshooting")
                
            print("="*60)
            
            return health_percentage >= 50
            
        except Exception as e:
            print(f"Health check error: {e}")
            return False
    
    def wait_for_services(self, max_wait_minutes=5):
        """Wait for services to start up"""
        print(f"\nWaiting for services to start (max {max_wait_minutes} minutes)...")
        
        for minute in range(max_wait_minutes):
            print(f"\nCheck {minute + 1}/{max_wait_minutes}:")
            
            all_healthy = True
            for name, port in self.services.items():
                try:
                    response = requests.get(f"http://localhost:{port}/health", timeout=3)
                    if response.status_code == 200:
                        print(f"  [OK] {name}")
                    else:
                        print(f"  [WAIT] {name} - Starting...")
                        all_healthy = False
                except:
                    print(f"  [WAIT] {name} - Starting...")
                    all_healthy = False
            
            if all_healthy:
                print(f"\n[SUCCESS] All services are healthy after {minute + 1} minute(s)!")
                return True
            
            if minute < max_wait_minutes - 1:
                print("Waiting 60 seconds for next check...")
                time.sleep(60)
        
        print(f"\n[WARNING] Some services still starting after {max_wait_minutes} minutes")
        return False

def main():
    """Main function"""
    monitor = SimpleSystemMonitor()
    
    print("AI Options Trading System - Simple Monitor")
    print("Choose an option:")
    print("1. Quick Health Check")
    print("2. Wait for Services to Start")
    print("3. Continuous Monitor (5 min intervals)")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == '1':
            monitor.quick_check()
        elif choice == '2':
            monitor.wait_for_services()
            monitor.quick_check()
        elif choice == '3':
            while True:
                monitor.quick_check()
                print("\nWaiting 5 minutes for next check...")
                time.sleep(300)
        else:
            print("Invalid choice, running quick check...")
            monitor.quick_check()
            
    except KeyboardInterrupt:
        print("\n\nMonitor stopped by user")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()