import {
  db,
  type ArchivoAdjuntoLocal,
  type ContactoLocal,
  type ComprobanteLocal,
  type ImputacionFiscalLocal,
  type IngresoLocal,
  type SyncQueueItem,
} from './db';
import { generateUUID } from '../utils/uuid';
import { useSyncStore } from '../stores/syncStore';
import { type ApiCategoria, mapCategoria } from '../hooks/useCategorias';

const BASE_URL = '/api/v1';
const BACKOFF_DELAYS = [1000, 5000, 15000, 30000, 60000];
export const MAX_RETRIES = 5;
const PULL_INTERVAL_MS = 5 * 60 * 1000;

interface PushResponse {
  aceptados: string[];
  rechazados: string[];
  conflictos: Array<{ registro_id: string; tabla: string; ganador: unknown }>;
  server_timestamp: string;
}

interface PullResponse {
  cambios: {
    contactos?: unknown[];
    comprobantes?: unknown[];
    imputaciones_fiscales?: unknown[];
    ingresos?: unknown[];
    adjuntos?: unknown[];
    categorias_irp?: unknown[];
  };
  server_timestamp: string;
  hay_mas: boolean;
}

let pullIntervalId: ReturnType<typeof setInterval> | null = null;
let retryTimeoutId: ReturnType<typeof setTimeout> | null = null;
let consecutiveFailures = 0;
let isPushing = false;
let isPulling = false;
let isOnline = typeof navigator !== 'undefined' ? navigator.onLine : true;

// --- sync_metadata helpers ---

async function getOrCreateDeviceId(): Promise<string> {
  const meta = await db.sync_metadata.get('metadata');
  if (meta?.device_id) return meta.device_id;
  const deviceId = generateUUID();
  await db.sync_metadata.put({
    key: 'metadata',
    device_id: deviceId,
    last_pull_timestamp: null,
    last_push_timestamp: null,
  });
  return deviceId;
}

async function getLastPullTimestamp(): Promise<string | null> {
  const meta = await db.sync_metadata.get('metadata');
  return meta?.last_pull_timestamp ?? null;
}

async function updateMeta(patch: Partial<{ last_pull_timestamp: string; last_push_timestamp: string }>): Promise<void> {
  const existing = await db.sync_metadata.get('metadata');
  if (existing) {
    await db.sync_metadata.update('metadata', patch);
  } else {
    await db.sync_metadata.put({
      key: 'metadata',
      device_id: generateUUID(),
      last_pull_timestamp: null,
      last_push_timestamp: null,
      ...patch,
    });
  }
}

// --- push ---

export async function push(): Promise<void> {
  if (!isOnline || isPushing) return;

  const pendingItems = await db.sync_queue
    .filter((item) => item.intentos < MAX_RETRIES)
    .toArray();

  if (pendingItems.length === 0) return;

  isPushing = true;
  try {
    const deviceId = await getOrCreateDeviceId();
    const dataItems = pendingItems.filter((i) => i.tabla !== 'adjuntos');
    const adjuntoItems = pendingItems.filter((i) => i.tabla === 'adjuntos');

    if (dataItems.length > 0) {
      await pushDataItems(dataItems, deviceId);
    }
    if (adjuntoItems.length > 0) {
      await pushAdjuntos(adjuntoItems);
    }

    await updateMeta({ last_push_timestamp: new Date().toISOString() });
  } finally {
    isPushing = false;
  }
}

async function pushDataItems(items: SyncQueueItem[], deviceId: string): Promise<void> {
  const body = {
    device_id: deviceId,
    cambios: items.map((item) => ({
      tabla: item.tabla,
      registro_id: item.registro_id,
      operacion: item.operacion,
      payload: item.payload,
      timestamp: item.timestamp,
    })),
  };

  let response: PushResponse;
  try {
    const res = await fetch(`${BASE_URL}/sync/push`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    response = await res.json();
    consecutiveFailures = 0;
  } catch (err) {
    consecutiveFailures++;
    await incrementRetries(items, String(err));
    scheduleRetry();
    return;
  }

  const aceptadosSet = new Set(response.aceptados);
  const conflictosSet = new Set(response.conflictos.map((c) => c.registro_id));

  for (const registroId of response.aceptados) {
    const item = items.find((i) => i.registro_id === registroId);
    if (item?.autoId != null) await db.sync_queue.delete(item.autoId);
    await markSynced(item!.tabla, registroId);
  }

  for (const conflicto of response.conflictos) {
    const item = items.find((i) => i.registro_id === conflicto.registro_id);
    if (item?.autoId != null) await db.sync_queue.delete(item.autoId);
    await applyConflictWinner(conflicto.tabla, conflicto.ganador);
  }

  const failedItems = items.filter(
    (i) => !aceptadosSet.has(i.registro_id) && !conflictosSet.has(i.registro_id)
  );
  if (failedItems.length > 0) {
    await incrementRetries(failedItems, 'rechazado por el servidor');
  }
}

async function pushAdjuntos(items: SyncQueueItem[]): Promise<void> {
  for (const item of items) {
    const adjunto = await db.adjuntos.get(item.registro_id);
    if (!adjunto?.blob) continue;

    const comprobante = await db.comprobantes.get(adjunto.comprobante_id);
    if (!comprobante || comprobante.sync_status !== 'synced') continue;

    try {
      const formData = new FormData();
      formData.append('adjunto_id', item.registro_id);
      formData.append('archivo', adjunto.blob, adjunto.nombre_archivo);

      const res = await fetch(`${BASE_URL}/comprobantes/${adjunto.comprobante_id}/adjuntos`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      await db.adjuntos.update(item.registro_id, { sync_status: 'synced' });
      if (item.autoId != null) await db.sync_queue.delete(item.autoId);
    } catch (err) {
      await incrementRetries([item], String(err));
    }
  }
}

// --- pull ---

export async function pull(): Promise<void> {
  if (!isOnline || isPulling) return;
  isPulling = true;

  try {
    const since = await getLastPullTimestamp();
    const url = since
      ? `${BASE_URL}/sync/pull?since=${encodeURIComponent(since)}`
      : `${BASE_URL}/sync/pull`;

    const res = await fetch(url);
    if (!res.ok) return;

    const data: PullResponse = await res.json();
    await applyPulledChanges(data.cambios);
    await updateMeta({ last_pull_timestamp: data.server_timestamp });
  } catch {
    // Network error — silently skip, will retry on next interval
  } finally {
    isPulling = false;
  }
}

async function applyPulledChanges(cambios: PullResponse['cambios']): Promise<void> {
  if (cambios.contactos?.length) {
    for (const r of cambios.contactos) {
      const registro = r as ContactoLocal;
      const existing = await db.contactos.get(registro.id);
      if (!existing || existing.updated_at < registro.updated_at) {
        await db.contactos.put({ ...registro, sync_status: 'synced' });
      }
    }
  }

  if (cambios.comprobantes?.length) {
    for (const r of cambios.comprobantes) {
      const registro = r as ComprobanteLocal;
      const existing = await db.comprobantes.get(registro.id);
      if (!existing || existing.updated_at < registro.updated_at) {
        await db.comprobantes.put({ ...registro, sync_status: 'synced' });
      }
    }
  }

  if (cambios.imputaciones_fiscales?.length) {
    for (const r of cambios.imputaciones_fiscales) {
      const registro = r as ImputacionFiscalLocal;
      const existing = await db.imputaciones.get(registro.id);
      if (!existing || existing.updated_at < registro.updated_at) {
        await db.imputaciones.put(registro);
      }
    }
  }

  if (cambios.ingresos?.length) {
    for (const r of cambios.ingresos) {
      const registro = r as IngresoLocal;
      const existing = await db.ingresos.get(registro.id);
      if (!existing || existing.updated_at < registro.updated_at) {
        await db.ingresos.put({ ...registro, sync_status: 'synced' });
      }
    }
  }

  if (cambios.adjuntos?.length) {
    for (const r of cambios.adjuntos) {
      const registro = r as Omit<ArchivoAdjuntoLocal, 'blob' | 'sync_status'>;
      const existing = await db.adjuntos.get(registro.id);
      if (!existing) {
        // Metadata only — blob se descarga bajo demanda
        await db.adjuntos.put({ ...registro, sync_status: 'synced' });
      }
    }
  }

  if (cambios.categorias_irp?.length) {
    const mapped = (cambios.categorias_irp as ApiCategoria[]).map(mapCategoria);
    await db.categorias_irp.clear();
    await db.categorias_irp.bulkPut(mapped);
  }
}

// --- helpers ---

async function markSynced(tabla: string, registroId: string): Promise<void> {
  switch (tabla) {
    case 'contactos':
      await db.contactos.update(registroId, { sync_status: 'synced' });
      break;
    case 'comprobantes':
      await db.comprobantes.update(registroId, { sync_status: 'synced' });
      break;
    case 'ingresos':
      await db.ingresos.update(registroId, { sync_status: 'synced' });
      break;
  }
}

async function applyConflictWinner(tabla: string, ganador: unknown): Promise<void> {
  switch (tabla) {
    case 'contactos':
      await db.contactos.put({ ...(ganador as ContactoLocal), sync_status: 'synced' });
      break;
    case 'comprobantes':
      await db.comprobantes.put({ ...(ganador as ComprobanteLocal), sync_status: 'synced' });
      break;
    case 'ingresos':
      await db.ingresos.put({ ...(ganador as IngresoLocal), sync_status: 'synced' });
      break;
    case 'imputaciones_fiscales':
      await db.imputaciones.put(ganador as ImputacionFiscalLocal);
      break;
  }
}

async function incrementRetries(items: SyncQueueItem[], error: string): Promise<void> {
  for (const item of items) {
    if (item.autoId != null) {
      await db.sync_queue.update(item.autoId, {
        intentos: item.intentos + 1,
        ultimo_error: error,
      });
    }
  }
}

function scheduleRetry(): void {
  if (retryTimeoutId) clearTimeout(retryTimeoutId);
  const delay = BACKOFF_DELAYS[Math.min(consecutiveFailures - 1, BACKOFF_DELAYS.length - 1)];
  retryTimeoutId = setTimeout(() => {
    retryTimeoutId = null;
    push();
  }, delay);
}

// --- on-demand blob download ---

export async function fetchAdjuntoBlob(adjuntoId: string): Promise<Blob | null> {
  const adjunto = await db.adjuntos.get(adjuntoId);
  if (adjunto?.blob) return adjunto.blob;
  if (!isOnline) return null;
  try {
    const res = await fetch(`${BASE_URL}/adjuntos/${adjuntoId}/download`);
    if (!res.ok) return null;
    const blob = await res.blob();
    await db.adjuntos.update(adjuntoId, { blob });
    return blob;
  } catch {
    return null;
  }
}

// --- cache cleanup ---

async function cleanupLocalCache(): Promise<void> {
  // Liberar blobs de adjuntos ya sincronizados (descarga on-demand si se necesitan)
  await db.adjuntos.where('sync_status').equals('synced').modify({ blob: undefined });

  // Eliminar de Dexie los registros borrados lógicamente que ya están confirmados en el servidor
  await db.comprobantes.filter(c => c.deleted_at != null && c.sync_status === 'synced').delete();
  await db.contactos.filter(c => c.deleted_at != null && c.sync_status === 'synced').delete();
  await db.ingresos.filter(i => i.deleted_at != null && i.sync_status === 'synced').delete();
}

// --- lifecycle ---

export async function syncAll(): Promise<void> {
  const store = useSyncStore.getState();
  store.setStatus('syncing');

  const beforePending = await db.sync_queue.filter((i) => i.intentos < MAX_RETRIES).count();

  await pull();
  await push();
  await cleanupLocalCache();

  const failedList = await db.sync_queue.filter((i) => i.intentos >= MAX_RETRIES).toArray();
  const afterPending = await db.sync_queue.filter((i) => i.intentos < MAX_RETRIES).count();
  store.setFailedItems(failedList);
  const now = new Date().toISOString();
  store.setLastSyncAt(now);

  if (failedList.length > 0) {
    store.setStatus('error');
    store.addToast('error', `${failedList.length} cambio${failedList.length > 1 ? 's' : ''} no pudo sincronizarse`);
  } else {
    store.setStatus('idle');
    if (beforePending > 0 && afterPending === 0) {
      store.addToast('success', 'Datos sincronizados');
    }
  }
}

function onOnline(): void {
  isOnline = true;
  useSyncStore.getState().setStatus('idle');
  push();
}

function onOffline(): void {
  isOnline = false;
  useSyncStore.getState().setStatus('offline');
}

export function startAutoSync(): void {
  if (pullIntervalId) return;

  window.addEventListener('online', onOnline);
  window.addEventListener('offline', onOffline);

  pullIntervalId = setInterval(() => {
    if (isOnline) syncAll();
  }, PULL_INTERVAL_MS);

  if (isOnline) syncAll();
}

export function stopAutoSync(): void {
  if (pullIntervalId) {
    clearInterval(pullIntervalId);
    pullIntervalId = null;
  }
  if (retryTimeoutId) {
    clearTimeout(retryTimeoutId);
    retryTimeoutId = null;
  }
  window.removeEventListener('online', onOnline);
  window.removeEventListener('offline', onOffline);
}

export const syncService = {
  push,
  pull,
  syncAll,
  startAutoSync,
  stopAutoSync,
  get isOnline() {
    return isOnline;
  },
};
