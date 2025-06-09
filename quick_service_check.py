#!/usr/bin/env python3
"""
Quick Service Status Check - Before Integration
"""

import requests
import time
from datetime import datetime

def check_service_status():
    """Quick check of all services before integration"""
    print("🔍 CURRENT SERVICE STATUS CHECK")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    services = {
        8001: "Data Acquisition",
        8002: "Technical Analysis", 
        8003: "ML Service",
        8004: "Strategy Engine",
        8005: "Risk Management",
        8006: "Options Analytics"
    }
    
    infrastructure = {
        5432: "PostgreSQL",
        6379: "Redis", 
        5678: "N8N"
    }
    
    working_services = 0
    
    # Check Python services
    print("PYTHON SERVICES:")
    print("-" * 20)
    for port, name in services.items():
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                uptime = data.get('uptime_seconds', 0)
                print(f"✅ {name:20} | Status: {status:8} | Uptime: {uptime:.0f}s")
                working_services += 1
            else:
                print(f"⚠️ {name:20} | HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {name:20} | NOT RESPONDING")
        except Exception as e:
            print(f"❌ {name:20} | ERROR: {str(e)[:30]}")
    
    print()
    print("INFRASTRUCTURE:")
    print("-" * 20)
    
    # Check PostgreSQL
    try:
        reader, writer = await_for(asyncio.open_connection('localhost', 5432), 3)
        writer.close()
        print("✅ PostgreSQL        | CONNECTED")
    except:
        print("❌ PostgreSQL        | NOT ACCESSIBLE")
    
    # Check Redis
    try:
        reader, writer = await_for(asyncio.open_connection('localhost', 6379), 3)
        writer.close()
        print("✅ Redis            | CONNECTED")
    except:
        print("❌ Redis            | NOT ACCESSIBLE")
    
    # Check N8N
    try:
        response = requests.get("http://localhost:5678/healthz", timeout=5)
        if response.status_code == 200:
            print("✅ N8N              | HEALTHY")
        else:
            print(f"⚠️ N8N              | HTTP {response.status_code}")
    except:
        print("❌ N8N              | NOT ACCESSIBLE")
    
    print()
    print("SUMMARY:")
    print("-" * 20)
    print(f"Working Services: {working_services}/6")
    
    if working_services >= 5:
        print("🎉 STATUS: EXCELLENT - Ready for integration")
        return "excellent"
    elif working_services >= 3:
        print("✅ STATUS: GOOD - Can proceed with integration")
        return "good"
    elif working_services >= 1:
        print("⚠️ STATUS: PARTIAL - Some services need restart")
        return "partial"
    else:
        print("❌ STATUS: CRITICAL - Services need to be started")
        return "critical"

def await_for(coro, timeout):
    """Simple timeout wrapper"""
    import asyncio
    try:
        return asyncio.wait_for(coro, timeout)
    except:
        raise ConnectionError("Timeout")

if __name__ == "__main__":
    status = check_service_status()
    
    print()
    print("NEXT STEPS:")
    print("-" * 20)
    
    if status == "critical":
        print("1. Start services: python start_all_services.py")
        print("2. Wait 30 seconds for startup")
        print("3. Re-run this check")
        print("4. Then proceed with integration")
    elif status == "partial":
        print("1. Restart failed services manually")
        print("2. Check service logs for errors")
        print("3. Then proceed with integration")
    else:
        print("1. ✅ Ready to run: python live_data_integration.py")
        print("2. This will fix N8N connectivity issues")
        print("3. Enable real-time market data")
    
    print()
    input("Press Enter when ready to proceed...")