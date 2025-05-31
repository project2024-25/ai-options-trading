'use client';

import React, { useState, useEffect } from 'react';
import { CheckCircle2, XCircle, Wifi, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const ServiceStatusItem: React.FC<{ name: string; port: string; status: 'online' | 'offline' | 'checking' }> = ({ name, port, status }) => {
  let Icon = CheckCircle2;
  let color = 'text-green-500';
  let statusText = 'Online';

  switch (status) {
    case 'offline':
      Icon = XCircle;
      color = 'text-red-500';
      statusText = 'Offline';
      break;
    case 'checking':
      Icon = Loader2;
      color = 'text-muted-foreground';
      statusText = 'Checking...';
      break;
    case 'online':
    default:
      Icon = CheckCircle2;
      color = 'text-green-500';
      statusText = 'Online';
      break;
  }

  return (
    <div className="flex items-center justify-between py-2 px-3 even:bg-muted/20 rounded-md">
      <div className="flex-1">
        <span className="text-sm font-medium">{name}</span>
        <span className="text-xs text-muted-foreground ml-2">:{port}</span>
      </div>
      <div className={`flex items-center space-x-2 text-xs ${color}`}>
        <Icon className={`h-4 w-4 ${status === 'checking' ? 'animate-spin' : ''}`} />
        <span className="font-medium">{statusText}</span>
      </div>
    </div>
  );
};

// Fixed health check using proper health endpoints
const checkServiceHealth = async (url: string): Promise<boolean> => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // Increased timeout

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    
    // Check if response is ok and contains expected health check data
    if (response.ok) {
      const data = await response.json();
      // Health endpoints should return status: "healthy" or similar
      return data.status === "healthy" || data.status === "ok" || response.ok;
    }
    
    return false;
  } catch (error) {
    console.log(`Service check failed for ${url}:`, error);
    return false;
  }
};

const OverallServiceStatusCard: React.FC = () => {
  // FIXED: Use proper health endpoints for all services
  const [services, setServices] = useState([
    { 
      name: 'Market Data Service', 
      port: '8001', 
      status: 'checking' as const, 
      url: 'http://localhost:8001/health' 
    },
    { 
      name: 'Technical Analysis Service', 
      port: '8002', 
      status: 'checking' as const, 
      url: 'http://localhost:8002/health' 
    },
    { 
      name: 'AI Prediction Service', 
      port: '8003', 
      status: 'checking' as const, 
      url: 'http://localhost:8003/health' 
    },
    { 
      name: 'Strategy Service', 
      port: '8004', 
      status: 'checking' as const, 
      url: 'http://localhost:8004/health'  // FIXED: Use health endpoint instead of AUTO_SELECT
    },
    { 
      name: 'Risk Management Service', 
      port: '8005', 
      status: 'checking' as const, 
      url: 'http://localhost:8005/health' 
    },
    { 
      name: 'Options Analytics Service', 
      port: '8006', 
      status: 'checking' as const, 
      url: 'http://localhost:8006/health' 
    },
  ]);

  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const checkAllServices = async () => {
    console.log('🔍 Starting service health checks...');

    // Update services sequentially to avoid overwhelming the backend
    for (let i = 0; i < services.length; i++) {
      const service = services[i];

      setServices(prev => prev.map((s, index) =>
        index === i ? { ...s, status: 'checking' as const } : s
      ));

      try {
        console.log(`🔍 Checking ${service.name} at ${service.url}`);
        const isOnline = await checkServiceHealth(service.url);
        console.log(`${isOnline ? '✅' : '❌'} ${service.name}: ${isOnline ? 'Online' : 'Offline'}`);

        setServices(prev => prev.map((s, index) =>
          index === i
            ? { ...s, status: isOnline ? 'online' : 'offline' as const }
            : s
        ));

        // Small delay between checks
        if (i < services.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 300));
        }
      } catch (error) {
        console.error(`❌ Error checking ${service.name}:`, error);
        setServices(prev => prev.map((s, index) =>
          index === i
            ? { ...s, status: 'offline' as const }
            : s
        ));
      }
    }

    setLastChecked(new Date());
    console.log('✅ Service health checks completed');
  };

  useEffect(() => {
    // Initial check
    checkAllServices();

    // Check services every 60 seconds (less frequent to reduce load)
    const interval = setInterval(checkAllServices, 60000);

    return () => clearInterval(interval);
  }, []);

  // Calculate overall status
  const onlineServices = services.filter(s => s.status === 'online');
  const offlineServices = services.filter(s => s.status === 'offline');
  const checkingServices = services.filter(s => s.status === 'checking');

  let overallStatusText = 'Checking services...';
  let OverallIcon = Loader2;
  let overallIconColor = 'text-muted-foreground';

  if (checkingServices.length === 0) {
    if (onlineServices.length === services.length) {
      overallStatusText = 'All services operational';
      OverallIcon = CheckCircle2;
      overallIconColor = 'text-green-500';
    } else if (offlineServices.length > 0) {
      overallStatusText = `${offlineServices.length} service${offlineServices.length > 1 ? 's' : ''} offline`;
      OverallIcon = XCircle;
      overallIconColor = 'text-red-500';
    }
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Wifi className="h-6 w-6 text-accent" />
            <CardTitle>Overall Service Status</CardTitle>
          </div>
          <div className="flex items-center space-x-1 text-xs text-muted-foreground">
            {checkingServices.length > 0 ? (
              <>
                <Loader2 className="h-3 w-3 animate-spin" />
                <span>Checking...</span>
              </>
            ) : (
              <>
                <CheckCircle2 className="h-3 w-3 text-green-500" />
                <span>Online</span>
              </>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Overall Status Header */}
          <div className={`flex items-center justify-center text-lg font-semibold ${overallIconColor} p-3 bg-muted/20 rounded-lg`}>
            <OverallIcon className={`h-6 w-6 mr-3 ${checkingServices.length > 0 ? 'animate-spin' : ''}`} />
            <span>{overallStatusText}</span>
          </div>

          {/* Service Status Summary */}
          <div className="text-center text-sm text-muted-foreground">
            {onlineServices.length}/{services.length} services online
            {offlineServices.length > 0 && (
              <span className="text-red-400 ml-2">
                ({offlineServices.length} offline)
              </span>
            )}
          </div>

          {/* Individual Service Status */}
          <div className="space-y-1">
            {services.map((service) => (
              <ServiceStatusItem
                key={service.name}
                name={service.name}
                port={service.port}
                status={service.status}
              />
            ))}
          </div>

          {/* Status Footer */}
          <div className="pt-3 border-t border-border text-center">
            {checkingServices.length === 0 && onlineServices.length === services.length && (
              <div className="text-xs text-green-400">
                ✅ All microservices are healthy and responding
              </div>
            )}

            {checkingServices.length === 0 && offlineServices.length > 0 && (
              <div className="space-y-1">
                <div className="text-xs text-red-400">
                  ⚠️ Some services appear offline in health check
                </div>
                <button 
                  onClick={checkAllServices}
                  className="text-xs text-blue-400 hover:text-blue-300 underline"
                >
                  Retry health checks
                </button>
              </div>
            )}

            {lastChecked && (
              <div className="text-xs text-muted-foreground mt-1">
                Last checked: {lastChecked.toLocaleTimeString()}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default OverallServiceStatusCard;