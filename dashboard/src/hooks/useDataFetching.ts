import { useState, useEffect, useCallback } from 'react';
import type { ApiError } from '@/types/api';

interface FetchState<T> {
  data: T | null;
  isLoading: boolean;
  error: ApiError | null;
  isOnline: boolean;
  lastUpdated: number | null; // Timestamp of last successful fetch
}

const REFRESH_INTERVAL = 30 * 1000; // 30 seconds

// Helper function to extract data from API response
function extractResponseData<T>(response: any): T {
  // Handle nested response format: { success: true, data: {...} }
  if (response && typeof response === 'object' && response.success && response.data) {
    return response.data as T;
  }
  
  // Handle direct response format: {...}
  if (response && typeof response === 'object' && !response.success) {
    return response as T;
  }
  
  // Fallback
  return response as T;
}

export function useDataFetching<T>(apiUrl: string, initialData: T | null = null): FetchState<T> {
  const [data, setData] = useState<T | null>(initialData);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [isOnline, setIsOnline] = useState<boolean>(true); // Assume online initially
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetch(apiUrl);
      if (!response.ok) {
        let errorData: ApiError;
        try {
            errorData = await response.json();
            if (!errorData.message) { // ensure message field exists
              errorData.message = `HTTP error! status: ${response.status}`;
            }
        } catch (e) {
            errorData = { message: `HTTP error! status: ${response.status}`, statusCode: response.status };
        }
        throw errorData;
      }
      
      const result = await response.json();
      
      // Extract the actual data from the response
      const extractedData = extractResponseData<T>(result);
      
      // Debug logging
      console.log(`API Response from ${apiUrl}:`, result);
      console.log(`Extracted data:`, extractedData);
      
      setData(extractedData);
      setError(null);
      setIsOnline(true);
      setLastUpdated(Date.now());
    } catch (err: any) {
      console.error(`Error fetching ${apiUrl}:`, err);
      
      if (err.message && typeof err.message === 'string') {
        setError({ message: err.message, statusCode: err.statusCode });
      } else {
        setError({ message: 'An unknown error occurred while fetching data.' });
      }
      setIsOnline(false);
      // Keep stale data if available, instead of setting data to null
      // setData(null); 
    } finally {
      setIsLoading(false);
    }
  }, [apiUrl]);

  useEffect(() => {
    fetchData(); // Initial fetch
    const intervalId = setInterval(fetchData, REFRESH_INTERVAL);
    return () => clearInterval(intervalId);
  }, [fetchData]);

  return { data, isLoading, error, isOnline, lastUpdated };
}