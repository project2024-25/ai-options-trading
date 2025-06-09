#!/usr/bin/env python3
"""
AI Options Trading System - Health Monitor
Monitors all services and provides system status
"""

import requests
import time
import logging
from datetime import datetime
import json
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system_health.log'),
        logging.StreamHandler()
    ]
)

class TradingSystemMonitor:
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
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                service_name = data.get('service', name)
                
                if status == 'healthy':
                    logging.info(f"✅ {name} (:{port}) - {status.upper()}")
                    return True, status
                else:
                    logging.warning(f"⚠️  {name} (:{port}) - {status.upper()}")
                    return True, status
            else:
                logging.error(f"❌ {name} (:{port}) - HTTP {response.status_code}")
                return False, f"HTTP {response.status_code}"
        except requests.exceptions.ConnectionError:
            logging.error(f"❌ {name} (:{port}) - CONNECTION REFUSED (Service not running)")
            return False, "NOT_RUNNING"
        except requests.exceptions.Timeout:
            logging.error(f"❌ {name} (:{port}) - TIMEOUT")
            return False, "TIMEOUT"
        except Exception as e:
            logging.error(f"❌ {name} (:{port}) - ERROR: {str(e)}")
            return False, str(e)
    
    def check_n8n_health(self):
        """Check N8N service health"""
        try:
            # Try main N8N endpoint
            response = requests.get(self.n8n_url, timeout=5)
            if response.status_code == 200:
                logging.info("✅ N8N - HEALTHY (Web interface accessible)")
                return True, "HEALTHY"
            else:
                logging.error(f"❌ N8N - HTTP {response.status_code}")
                return False, f"HTTP {response.status_code}"
        except requests.exceptions.ConnectionError:
            logging.error("❌ N8N - CONNECTION REFUSED (Service not running)")
            return False, "NOT_RUNNING"
        except requests.exceptions.Timeout:
            logging.error("❌ N8N - TIMEOUT")
            return False, "TIMEOUT"
        except Exception as e:
            logging.error(f"❌ N8N - ERROR: {str(e)}")
            return False, str(e)
    
    def check_kite_connection(self):
        """Check if Kite API connection is working"""
        try:
            response = requests.get("http://localhost:8001/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                kite_status = data.get('checks', {}).get('kite', 'unknown')
                
                if isinstance(kite_status, dict):
                    if kite_status.get('status') == 'connected':
                        user = kite_status.get('user', 'Unknown')
                        user_id = kite_status.get('user_id', '')
                        mode = kite_status.get('mode', 'unknown')
                        logging.info(f"✅ Kite API - CONNECTED (User: {user}, ID: {user_id}, Mode: {mode})")
                        return True, f"Connected as {user} ({mode})"
                    else:
                        error_msg = kite_status.get('error', 'Connection failed')
                        logging.warning(f"⚠️  Kite API - {error_msg}")
                        return False, error_msg
                else:
                    if kite_status == 'not_configured':
                        logging.warning("⚠️  Kite API - NOT CONFIGURED (Run zerodha_setup.py)")
                        return False, "Not configured - run zerodha_setup.py"
                    else:
                        logging.warning(f"⚠️  Kite API - {kite_status}")
                        return False, str(kite_status)
        except Exception as e:
            logging.error(f"❌ Kite API - ERROR: {str(e)}")
            return False, str(e)
    
    def check_market_hours(self):
        """Check if markets are open"""
        try:
            response = requests.get("http://localhost:8001/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                market_status = data.get('checks', {}).get('market_hours', 'unknown')
                
                if market_status == 'open':
                    logging.info("✅ Market Hours - OPEN")
                    return True, "OPEN"
                else:
                    logging.info(f"ℹ️  Market Hours - {market_status.upper()}")
                    return True, market_status.upper()
        except Exception as e:
            logging.warning(f"⚠️  Market Hours - Cannot determine: {str(e)}")
            return False, "UNKNOWN"
    
    def full_system_check(self):
        """Perform complete system health check"""
        print("\n" + "="*70)
        print(f"🤖 AI OPTIONS TRADING SYSTEM - HEALTH CHECK")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        all_healthy = True
        service_status = {}
        
        # Check Python services
        print("\n🔧 PYTHON SERVICES:")
        print("-" * 40)
        for name, port in self.services.items():
            healthy, status = self.check_service_health(name, port)
            service_status[name] = {'healthy': healthy, 'status': status}
            if not healthy:
                all_healthy = False
        
        # Check N8N
        print("\n🔄 WORKFLOW ENGINE:")
        print("-" * 40)
        n8n_healthy, n8n_status = self.check_n8n_health()
        service_status['N8N'] = {'healthy': n8n_healthy, 'status': n8n_status}
        if not n8n_healthy:
            all_healthy = False
        
        # Check Kite API
        print("\n📡 MARKET DATA:")
        print("-" * 40)
        kite_healthy, kite_status = self.check_kite_connection()
        service_status['Kite API'] = {'healthy': kite_healthy, 'status': kite_status}
        
        # Check Market Hours
        market_healthy, market_status = self.check_market_hours()
        service_status['Market Hours'] = {'healthy': market_healthy, 'status': market_status}
        
        # Overall status
        print("\n" + "="*70)
        if all_healthy:
            print("🟢 OVERALL STATUS: ALL SYSTEMS OPERATIONAL")
            print("✅ Ready for trading operations")
        else:
            print("🔴 OVERALL STATUS: ISSUES DETECTED")
            print("⚠️  Some services need attention")
        
        print("="*70)
        
        # Summary
        print(f"\n📊 SUMMARY:")
        healthy_count = sum(1 for status in service_status.values() if status['healthy'])
        total_count = len(service_status)
        print(f"   • Services Running: {healthy_count}/{total_count}")
        print(f"   • Market Status: {market_status}")
        print(f"   • Kite API: {kite_status}")
        print(f"   • System Health: {'GOOD' if all_healthy else 'NEEDS ATTENTION'}")
        
        return all_healthy, service_status
    
    def quick_check(self):
        """Quick health check without detailed output"""
        try:
            healthy_services = 0
            total_services = len(self.services) + 1  # +1 for N8N
            
            # Check Python services
            for name, port in self.services.items():
                try:
                    response = requests.get(f"http://localhost:{port}/health", timeout=3)
                    if response.status_code == 200:
                        healthy_services += 1
                except:
                    pass
            
            # Check N8N
            try:
                response = requests.get(self.n8n_url, timeout=3)
                if response.status_code == 200:
                    healthy_services += 1
            except:
                pass
            
            health_percentage = (healthy_services / total_services) * 100
            print(f"System Health: {healthy_services}/{total_services} services ({health_percentage:.1f}%)")
            
            return health_percentage >= 85  # Consider healthy if 85%+ services are up
            
        except Exception as e:
            print(f"Health check error: {e}")
            return False
    
    def continuous_monitoring(self, interval_minutes=15):
        """Run continuous monitoring"""
        print(f"Starting continuous monitoring (every {interval_minutes} minutes)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.full_system_check()
                print(f"\n⏱️  Waiting {interval_minutes} minutes for next check...")
                time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Monitoring error: {e}")

def main():
    """Main function"""
    monitor = TradingSystemMonitor()
    
    print("🤖 AI Options Trading System Monitor")
    print("Choose an option:")
    print("1. Full System Check")
    print("2. Quick Health Check")
    print("3. Continuous Monitoring (15 min intervals)")
    print("4. Continuous Monitoring (5 min intervals)")
    
    try:
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            monitor.full_system_check()
        elif choice == '2':
            monitor.quick_check()
        elif choice == '3':
            monitor.continuous_monitoring(15)
        elif choice == '4':
            monitor.continuous_monitoring(5)
        else:
            print("Invalid choice, running full system check...")
            monitor.full_system_check()
            
    except KeyboardInterrupt:
        print("\n\n👋 Monitor stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()