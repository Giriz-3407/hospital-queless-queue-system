import { useState, useEffect, useCallback } from 'react';
import { QueueTicket } from '../types';
import { queueService } from '../services/queueService';

export function useQueue(pollIntervalMs: number = 10000) {
  const [queues, setQueues] = useState<QueueTicket[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchQueues = useCallback(async () => {
    try {
      const data = await queueService.getMyQueues();
      setQueues(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch queue data');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchQueues();
    if (pollIntervalMs > 0) {
      const timer = setInterval(fetchQueues, pollIntervalMs);
      return () => clearInterval(timer);
    }
  }, [fetchQueues, pollIntervalMs]);

  const activeTicket = queues.find((q) => q.status === 'waiting' || q.status === 'in_consultation');

  return {
    queues,
    activeTicket,
    isLoading,
    error,
    refresh: fetchQueues,
  };
}
