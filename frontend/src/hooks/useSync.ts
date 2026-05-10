import { useEffect } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../services/db';
import { startAutoSync, stopAutoSync } from '../services/sync';
import { useSyncStore } from '../stores/syncStore';

const MAX_RETRIES = 5;

export function useSync() {
  const { setPendingCount, setFailedItems } = useSyncStore();

  const queueItems = useLiveQuery(() => db.sync_queue.toArray(), []);

  useEffect(() => {
    if (!queueItems) return;
    setPendingCount(queueItems.filter((i) => i.intentos < MAX_RETRIES).length);
    setFailedItems(queueItems.filter((i) => i.intentos >= MAX_RETRIES));
  }, [queueItems, setPendingCount, setFailedItems]);

  useEffect(() => {
    startAutoSync();
    return () => stopAutoSync();
  }, []);
}
