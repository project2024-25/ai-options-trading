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
      setData(result);
      setError(null);
      setIsOnline(true);
      setLastUpdated(Date.now());
    } catch (err: any) {
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
