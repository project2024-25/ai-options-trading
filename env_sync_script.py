#!/usr/bin/env python3
"""
Environment Files Synchronization Script
Sync fresh Kite credentials across all .env files
"""

import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

class EnvSynchronizer:
    def __init__(self):
        self.root_dir = Path.cwd()
        self.env_files = []
        
    def find_all_env_files(self):
        """Find all .env files in the project"""
        print("🔍 FINDING ALL .ENV FILES")
        print("=" * 30)
        
        # Look for .env files recursively
        for env_file in self.root_dir.rglob(".env"):
            self.env_files.append(env_file)
            relative_path = env_file.relative_to(self.root_dir)
            print(f"Found: {relative_path}")
        
        # Also check for .env.template files
        template_files = list(self.root_dir.rglob(".env.template"))
        if template_files:
            print("\nTemplate files found:")
            for template in template_files:
                relative_path = template.relative_to(self.root_dir)
                print(f"Template: {relative_path}")
        
        print(f"\nTotal .env files found: {len(self.env_files)}")
        return self.env_files
    
    def read_env_file(self, env_path):
        """Read and parse an .env file"""
        try:
            with open(env_path, 'r') as f:
                content = f.read()
            
            # Parse key-value pairs
            config = {}
            for line in content.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
            
            return config, content
        except Exception as e:
            print(f"Error reading {env_path}: {e}")
            return {}, ""
    
    def get_master_config(self):
        """Get the most complete configuration (from root .env)"""
        print("\n📋 ANALYZING CONFIGURATIONS")
        print("=" * 35)
        
        # Load from root .env (should have fresh credentials)
        root_env = self.root_dir / ".env"
        if root_env.exists():
            load_dotenv(root_env, override=True)
            
            # Get fresh credentials
            master_config = {
                'KITE_API_KEY': os.getenv('KITE_API_KEY', ''),
                'KITE_ACCESS_TOKEN': os.getenv('KITE_ACCESS_TOKEN', ''),
                'KITE_API_SECRET': os.getenv('KITE_API_SECRET', ''),
                'DATABASE_URL': os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/options_trading'),
                'REDIS_URL': os.getenv('REDIS_URL', 'redis://localhost:6379'),
                'DATA_ACQUISITION_PORT': os.getenv('DATA_ACQUISITION_PORT', '8001'),
                'TECHNICAL_ANALYSIS_PORT': os.getenv('TECHNICAL_ANALYSIS_PORT', '8002'),
                'ML_SERVICE_PORT': os.getenv('ML_SERVICE_PORT', '8003'),
                'STRATEGY_ENGINE_PORT': os.getenv('STRATEGY_ENGINE_PORT', '8004'),
                'RISK_MANAGEMENT_PORT': os.getenv('RISK_MANAGEMENT_PORT', '8005'),
                'OPTIONS_ANALYTICS_PORT': os.getenv('OPTIONS_ANALYTICS_PORT', '8006'),
                'ORDER_EXECUTION_PORT': os.getenv('ORDER_EXECUTION_PORT', '8007'),
                'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
                'PAPER_TRADING': os.getenv('PAPER_TRADING', 'true'),
                'MAX_RISK_PER_TRADE': os.getenv('MAX_RISK_PER_TRADE', '0.02'),
                'MAX_PORTFOLIO_RISK': os.getenv('MAX_PORTFOLIO_RISK', '0.10'),
                'GOOGLE_SHEETS_SPREADSHEET_ID': os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID', '1WM6NrthrfDDFD8HWEdh1cTcsrAH-DK31hekKY6GPMMo'),
                'SLACK_BOT_TOKEN': os.getenv('SLACK_BOT_TOKEN', 'webhook_mode'),
                'N8N_WEBHOOK_URL': os.getenv('N8N_WEBHOOK_URL', 'http://localhost:5678')
            }
            
            print(f"Master config loaded from: {root_env}")
            print(f"✅ Kite API Key: {master_config['KITE_API_KEY'][:10]}..." if master_config['KITE_API_KEY'] else "❌ No API Key")
            print(f"✅ Access Token: {master_config['KITE_ACCESS_TOKEN'][:15]}..." if master_config['KITE_ACCESS_TOKEN'] else "❌ No Access Token")
            
            return master_config
        else:
            print("❌ No root .env file found!")
            return {}
    
    def create_env_content(self, config):
        """Create standardized .env file content"""
        content = """# AI Options Trading System Configuration
# Auto-generated and synchronized

# Zerodha Kite API Configuration
KITE_API_KEY={KITE_API_KEY}
KITE_ACCESS_TOKEN={KITE_ACCESS_TOKEN}
KITE_API_SECRET={KITE_API_SECRET}

# Database Configuration
DATABASE_URL={DATABASE_URL}
REDIS_URL={REDIS_URL}

# Service Ports
DATA_ACQUISITION_PORT={DATA_ACQUISITION_PORT}
TECHNICAL_ANALYSIS_PORT={TECHNICAL_ANALYSIS_PORT}
ML_SERVICE_PORT={ML_SERVICE_PORT}
STRATEGY_ENGINE_PORT={STRATEGY_ENGINE_PORT}
RISK_MANAGEMENT_PORT={RISK_MANAGEMENT_PORT}
OPTIONS_ANALYTICS_PORT={OPTIONS_ANALYTICS_PORT}
ORDER_EXECUTION_PORT={ORDER_EXECUTION_PORT}

# Trading Configuration
PAPER_TRADING={PAPER_TRADING}
MAX_RISK_PER_TRADE={MAX_RISK_PER_TRADE}
MAX_PORTFOLIO_RISK={MAX_PORTFOLIO_RISK}

# Integration Configuration
GOOGLE_SHEETS_SPREADSHEET_ID={GOOGLE_SHEETS_SPREADSHEET_ID}
SLACK_BOT_TOKEN={SLACK_BOT_TOKEN}
N8N_WEBHOOK_URL={N8N_WEBHOOK_URL}

# System Configuration
LOG_LEVEL={LOG_LEVEL}
DEBUG_MODE=true
STARTUP_TIMEOUT=30
""".format(**config)
        
        return content
    
    def sync_all_env_files(self, master_config):
        """Synchronize all .env files with master configuration"""
        print("\n🔄 SYNCHRONIZING ALL .ENV FILES")
        print("=" * 40)
        
        standardized_content = self.create_env_content(master_config)
        
        synced_count = 0
        for env_file in self.env_files:
            try:
                # Backup original
                backup_file = env_file.with_suffix('.env.backup')
                if env_file.exists():
                    shutil.copy2(env_file, backup_file)
                    print(f"  📄 Backed up: {env_file.name} → {backup_file.name}")
                
                # Write synchronized content
                with open(env_file, 'w') as f:
                    f.write(standardized_content)
                
                relative_path = env_file.relative_to(self.root_dir)
                print(f"  ✅ Synced: {relative_path}")
                synced_count += 1
                
            except Exception as e:
                print(f"  ❌ Failed to sync {env_file}: {e}")
        
        print(f"\n📊 Synchronization complete: {synced_count}/{len(self.env_files)} files synced")
        return synced_count
    
    def verify_synchronization(self):
        """Verify that all .env files have the same credentials"""
        print("\n🔍 VERIFYING SYNCHRONIZATION")
        print("=" * 35)
        
        credentials_match = True
        reference_token = None
        
        for env_file in self.env_files:
            try:
                # Load this .env file
                load_dotenv(env_file, override=True)
                token = os.getenv('KITE_ACCESS_TOKEN', '')
                
                if not reference_token:
                    reference_token = token
                
                relative_path = env_file.relative_to(self.root_dir)
                
                if token == reference_token and token:
                    print(f"  ✅ {relative_path}: Token matches")
                elif not token:
                    print(f"  ⚠️ {relative_path}: No token found")
                    credentials_match = False
                else:
                    print(f"  ❌ {relative_path}: Token mismatch")
                    credentials_match = False
                    
            except Exception as e:
                print(f"  ❌ {env_file}: Verification failed - {e}")
                credentials_match = False
        
        if credentials_match and reference_token:
            print(f"\n✅ All .env files synchronized with token: {reference_token[:15]}...")
        else:
            print(f"\n⚠️ Some .env files may need manual attention")
        
        return credentials_match
    
    def restart_data_acquisition_service(self):
        """Restart Data Acquisition service to pick up new credentials"""
        print("\n🔄 RESTARTING DATA ACQUISITION SERVICE")
        print("=" * 45)
        
        try:
            import subprocess
            import sys
            import time
            
            # Kill existing process on port 8001
            try:
                import psutil
                for proc in psutil.process_iter(['pid', 'name', 'connections']):
                    try:
                        for conn in proc.info['connections']:
                            if conn.laddr.port == 8001:
                                proc.terminate()
                                time.sleep(2)
                                if proc.is_running():
                                    proc.kill()
                                print("  ✅ Terminated existing Data Acquisition process")
                                break
                    except:
                        continue
            except ImportError:
                print("  ⚠️ psutil not available, manual process cleanup may be needed")
            
            # Start new process
            service_path = self.root_dir / "services" / "data-acquisition" / "app"
            if service_path.exists() and (service_path / "main.py").exists():
                env = os.environ.copy()
                env["PYTHONPATH"] = str(self.root_dir)
                
                process = subprocess.Popen(
                    [sys.executable, "main.py"],
                    cwd=str(service_path),
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                print(f"  🚀 Started Data Acquisition service (PID: {process.pid})")
                
                # Wait and test
                time.sleep(10)
                
                import requests
                try:
                    response = requests.get("http://localhost:8001/health", timeout=10)
                    if response.status_code == 200:
                        print("  ✅ Service restarted successfully")
                        
                        # Test live data
                        data_response = requests.get("http://localhost:8001/api/data/nifty-snapshot", timeout=10)
                        if data_response.status_code == 200:
                            data = data_response.json()
                            if data.get('source') != 'mock_data':
                                print(f"  🎉 LIVE DATA CONFIRMED: NIFTY at ₹{data.get('data', {}).get('ltp', 'N/A')}")
                            else:
                                print("  ⚠️ Still using mock data (may be outside market hours)")
                        
                        return True
                    else:
                        print(f"  ❌ Service health check failed: HTTP {response.status_code}")
                        return False
                except Exception as e:
                    print(f"  ❌ Service test failed: {e}")
                    return False
            else:
                print("  ❌ Service directory or main.py not found")
                return False
                
        except Exception as e:
            print(f"  ❌ Restart failed: {e}")
            return False
    
    def run_full_sync(self):
        """Run complete environment synchronization"""
        print("🔄 ENVIRONMENT SYNCHRONIZATION")
        print("=" * 35)
        
        # Find all .env files
        self.find_all_env_files()
        
        if not self.env_files:
            print("❌ No .env files found!")
            return False
        
        # Get master configuration
        master_config = self.get_master_config()
        if not master_config.get('KITE_ACCESS_TOKEN'):
            print("❌ No valid credentials found in master config!")
            return False
        
        # Sync all files
        synced_count = self.sync_all_env_files(master_config)
        
        # Verify synchronization
        verification_success = self.verify_synchronization()
        
        # Restart service
        restart_success = self.restart_data_acquisition_service()
        
        # Final summary
        print("\n" + "=" * 50)
        print("SYNCHRONIZATION SUMMARY")
        print("=" * 50)
        print(f"Files found: {len(self.env_files)}")
        print(f"Files synced: {synced_count}")
        print(f"Verification: {'✅ PASSED' if verification_success else '❌ FAILED'}")
        print(f"Service restart: {'✅ SUCCESS' if restart_success else '❌ FAILED'}")
        
        overall_success = synced_count > 0 and verification_success
        
        if overall_success:
            print("\n🎉 SYNCHRONIZATION COMPLETED SUCCESSFULLY!")
            print("All .env files now have fresh Kite API credentials")
            print("Data Acquisition service should now use live data")
        else:
            print("\n⚠️ SYNCHRONIZATION HAD ISSUES")
            print("Check individual .env files and service logs")
        
        return overall_success

if __name__ == "__main__":
    print("🔄 ENVIRONMENT FILES SYNCHRONIZATION")
    print("=" * 40)
    print("This will sync fresh Kite credentials across all .env files")
    print()
    
    synchronizer = EnvSynchronizer()
    
    try:
        success = synchronizer.run_full_sync()
        
        if success:
            print("\n🚀 READY FOR LIVE DATA TESTING!")
            print("Run: curl http://localhost:8001/api/data/nifty-snapshot")
            print("Then: python live_trading_transition.py")
        else:
            print("\n🔧 MANUAL INTERVENTION MAY BE NEEDED")
            print("Check .env files and restart services manually")
            
    except KeyboardInterrupt:
        print("\n⏹️ Synchronization interrupted")
    except Exception as e:
        print(f"\n❌ Synchronization failed: {e}")
    
    print("\nSynchronization completed.")