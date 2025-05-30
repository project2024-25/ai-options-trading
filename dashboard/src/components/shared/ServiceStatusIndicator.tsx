import type React from 'react';
import { CheckCircle2, XCircle, Loader2, WifiOff } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from '@/components/ui/tooltip';

interface ServiceStatusIndicatorProps {
  isOnline: boolean;
  isLoading: boolean;
  lastUpdated?: number | null;
  serviceName?: string;
}

const ServiceStatusIndicator: React.FC<ServiceStatusIndicatorProps> = ({
  isOnline,
  isLoading,
  lastUpdated,
  serviceName = 'Service',
}) => {
  let statusText: string;
  let IconComponent: React.ElementType;
  let iconColorClass: string;

  if (isLoading) {
    statusText = `${serviceName} is updating...`;
    IconComponent = Loader2;
    iconColorClass = 'text-muted-foreground animate-spin';
  } else if (isOnline) {
    statusText = `${serviceName} is online.`;
    IconComponent = CheckCircle2;
    iconColorClass = 'text-green-500';
  } else {
    statusText = `${serviceName} is offline or experiencing issues.`;
    IconComponent = WifiOff;
    iconColorClass = 'text-destructive';
  }
  
  const timeAgo = lastUpdated ? Math.round((Date.now() - lastUpdated) / 1000) : null;

  return (
    <TooltipProvider>
      <Tooltip delayDuration={100}>
        <TooltipTrigger asChild>
          <div className="flex items-center space-x-1 text-xs text-muted-foreground">
            <IconComponent className={`h-3 w-3 ${iconColorClass}`} />
            {isLoading ? (
              <span>Updating...</span>
            ) : isOnline ? (
              <span>{timeAgo !== null ? `Updated ${timeAgo}s ago` : 'Online'}</span>
            ) : (
              <span>Offline</span>
            )}
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <p>{statusText}</p>
          {lastUpdated && isOnline && !isLoading && (
            <p>Last successful update: {new Date(lastUpdated).toLocaleTimeString()}</p>
          )}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

export default ServiceStatusIndicator;
