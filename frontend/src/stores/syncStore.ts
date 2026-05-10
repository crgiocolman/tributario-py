import { create } from 'zustand';
import type { SyncQueueItem } from '../services/db';

export type SyncStatus = 'idle' | 'syncing' | 'error' | 'offline';

export interface Toast {
  id: string;
  type: 'success' | 'error';
  message: string;
}

interface SyncStore {
  status: SyncStatus;
  pendingCount: number;
  failedItems: SyncQueueItem[];
  lastSyncAt: string | null;
  toasts: Toast[];
  setStatus: (status: SyncStatus) => void;
  setPendingCount: (n: number) => void;
  setFailedItems: (items: SyncQueueItem[]) => void;
  setLastSyncAt: (ts: string) => void;
  addToast: (type: Toast['type'], message: string) => void;
  removeToast: (id: string) => void;
}

export const useSyncStore = create<SyncStore>((set) => ({
  status: typeof navigator !== 'undefined' && navigator.onLine ? 'idle' : 'offline',
  pendingCount: 0,
  failedItems: [],
  lastSyncAt: null,
  toasts: [],

  setStatus: (status) => set({ status }),
  setPendingCount: (pendingCount) => set({ pendingCount }),
  setFailedItems: (failedItems) => set({ failedItems }),
  setLastSyncAt: (lastSyncAt) => set({ lastSyncAt }),

  addToast: (type, message) => {
    const id = crypto.randomUUID();
    set((s) => ({ toasts: [...s.toasts, { id, type, message }] }));
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
    }, 3500);
  },

  removeToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));
