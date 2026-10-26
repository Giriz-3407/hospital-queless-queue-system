import { useState, useEffect, useCallback, useRef } from 'react';
import { QueueTicket } from '../types';
import { queueService } from '../services/queueService';

export function useQueue(pollIntervalMs: number = 10000) {
  const [queues, setQueues] = useState<QueueTicket[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const isVisibleRef = useRef<boolean>(true);

  const fetchQueues = useCallback(async (isBackground: boolean = false) => {
    // Skip polling if document is hidden
    if (typeof document !== 'undefined' && document.visibilityState === 'hidden') {
      return;
    }

    try {
      if (!isBackground) {
        setIsLoading((prev) => (queues.length === 0 ? true : prev));
      }
      const data = await queueService.getMyQueues();
      setQueues(data);
      setError(null);
    } catch (err: any) {
      // Keep existing queues data on background network failure
      setError(err.message || 'Failed to fetch queue data');
    } finally {
      setIsLoading(false);
    }
  }, [queues.length]);

  useEffect(() => {
    // Initial fetch
    fetchQueues(false);

    // Visibility change handler to pause polling when tab is hidden
    const handleVisibilityChange = () => {
      const isVisible = document.visibilityState === 'visible';
      isVisibleRef.current = isVisible;
      if (isVisible) {
        fetchQueues(true);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Polling interval
    let timer: NodeJS.Timeout | null = null;
    if (pollIntervalMs > 0) {
      timer = setInterval(() => {
        if (isVisibleRef.current) {
          fetchQueues(true);
        }
      }, pollIntervalMs);
    }

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      if (timer) clearInterval(timer);
    };
  }, [fetchQueues, pollIntervalMs]);

  const activeTicket = queues.find((q) => {
    const s = (q.status || '').toLowerCase();
    return s === 'waiting' || s === 'called' || s === 'in_consultation';
  });

  return {
    queues,
    activeTicket,
    isLoading,
    error,
    refresh: () => fetchQueues(false),
  };
}
