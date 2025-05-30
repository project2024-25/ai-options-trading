import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import ServiceStatusIndicator from './ServiceStatusIndicator';
import { Loader2, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CardWrapperProps {
  title: string;
  description?: string;
  icon?: React.ElementType;
  isLoading: boolean;
  error: { message: string } | null;
  isOnline: boolean;
  lastUpdated: number | null;
  children: React.ReactNode;
  className?: string;
  contentClassName?: string;
  serviceName?: string;
}

const CardWrapper: React.FC<CardWrapperProps> = ({
  title,
  description,
  icon: Icon,
  isLoading,
  error,
  isOnline,
  lastUpdated,
  children,
  className,
  contentClassName,
  serviceName
}) => {
  const [isPulsing, setIsPulsing] = React.useState(false);

  React.useEffect(() => {
    if (lastUpdated) {
      setIsPulsing(true);
      const timer = setTimeout(() => setIsPulsing(false), 1500); // Corresponds to animation duration
      return () => clearTimeout(timer);
    }
  }, [lastUpdated]);

  return (
    <Card className={cn("flex flex-col", className, isPulsing && !isLoading && isOnline && 'animate-pulse-subtle')}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {Icon && <Icon className="h-6 w-6 text-accent" />}
            <CardTitle>{title}</CardTitle>
          </div>
          <ServiceStatusIndicator isLoading={isLoading} isOnline={isOnline} lastUpdated={lastUpdated} serviceName={serviceName || title} />
        </div>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent className={cn("flex-grow", contentClassName)}>
        {isLoading && !lastUpdated && ( // Show loader only on initial load or if no data yet
          <div className="flex flex-col items-center justify-center h-full min-h-[150px] text-muted-foreground">
            <Loader2 className="h-8 w-8 animate-spin mb-2" />
            <p>Loading {title}...</p>
          </div>
        )}
        {!isLoading && error && !isOnline && ( // Show error if not loading, error exists, and offline
             <div className="flex flex-col items-center justify-center h-full min-h-[150px] text-destructive">
             <AlertTriangle className="h-8 w-8 mb-2" />
             <p className="font-semibold">Error loading {title}</p>
             <p className="text-xs">{error.message}</p>
           </div>
        )}
        {(!isLoading && isOnline) || (lastUpdated && !error) ? children : null} 
        {/* Show children if not loading and online, OR if there's existing data even if current fetch failed but was previously online */}
        {/* If loading but there's old data, show old data (children) and status indicator shows loading */}
         {isLoading && lastUpdated && children}
      </CardContent>
    </Card>
  );
};

export default CardWrapper;
