import { useEffect, useRef, useState } from 'react';
import { db, type SyncQueueItem } from '../../services/db';
import { push, syncAll, MAX_RETRIES } from '../../services/sync';
import { useSyncStore, type SyncStatus } from '../../stores/syncStore';

function formatRelative(iso: string): string {
  const mins = Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
  if (mins < 1) return 'justo ahora';
  if (mins < 60) return `hace ${mins} min`;
  const h = Math.floor(mins / 60);
  if (h < 24) return `hace ${h}h`;
  return `hace ${Math.floor(h / 24)}d`;
}

function SyncIcon({ status }: { status: SyncStatus }) {
  const cls = 'w-5 h-5';
  if (status === 'offline') {
    return (
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className={cls}>
        <path fillRule="evenodd" d="M1.606 6.08a10.5 10.5 0 0115.906-1.83M3.457 9.098A7.5 7.5 0 0115 8.321M10.5 17.25a3 3 0 100-6 3 3 0 000 6zm10.44-9.44a.75.75 0 010 1.06l-3 3a.75.75 0 01-1.06-1.06l1.72-1.72H15a.75.75 0 010-1.5h3.44l-1.72-1.72a.75.75 0 011.06-1.06l3 3z" clipRule="evenodd" />
      </svg>
    );
  }
  if (status === 'syncing') {
    return (
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className={`${cls} animate-spin`}>
        <path fillRule="evenodd" d="M4.755 10.059a7.5 7.5 0 0112.548-3.364l1.903 1.903h-3.183a.75.75 0 100 1.5h4.992a.75.75 0 00.75-.75V4.356a.75.75 0 00-1.5 0v3.18l-1.9-1.9A9 9 0 003.306 9.67a.75.75 0 101.45.388zm15.408 3.352a.75.75 0 00-.919.53 7.5 7.5 0 01-12.548 3.364l-1.902-1.903h3.183a.75.75 0 000-1.5H2.984a.75.75 0 00-.75.75v4.992a.75.75 0 001.5 0v-3.18l1.9 1.9a9 9 0 0015.059-4.035.75.75 0 00-.53-.918z" clipRule="evenodd" />
      </svg>
    );
  }
  if (status === 'error') {
    return (
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className={cls}>
        <path fillRule="evenodd" d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm8.706-1.442c1.146-.573 2.437.463 2.126 1.706l-.709 2.836.042-.02a.75.75 0 01.67 1.34l-.04.022c-1.147.573-2.438-.463-2.127-1.706l.71-2.836-.042.02a.75.75 0 11-.671-1.34l.041-.022zM12 9a.75.75 0 100-1.5.75.75 0 000 1.5z" clipRule="evenodd" />
      </svg>
    );
  }
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className={cls}>
      <path fillRule="evenodd" d="M4.755 10.059a7.5 7.5 0 0112.548-3.364l1.903 1.903h-3.183a.75.75 0 100 1.5h4.992a.75.75 0 00.75-.75V4.356a.75.75 0 00-1.5 0v3.18l-1.9-1.9A9 9 0 003.306 9.67a.75.75 0 101.45.388zm15.408 3.352a.75.75 0 00-.919.53 7.5 7.5 0 01-12.548 3.364l-1.902-1.903h3.183a.75.75 0 000-1.5H2.984a.75.75 0 00-.75.75v4.992a.75.75 0 001.5 0v-3.18l1.9 1.9a9 9 0 0015.059-4.035.75.75 0 00-.53-.918z" clipRule="evenodd" />
    </svg>
  );
}

const STATUS_COLOR: Record<SyncStatus, string> = {
  idle: 'text-slate-400',
  syncing: 'text-blue-400',
  error: 'text-red-400',
  offline: 'text-slate-600',
};

const STATUS_LABEL: Record<SyncStatus, string> = {
  idle: 'Sincronizado',
  syncing: 'Sincronizando...',
  error: 'Errores de sync',
  offline: 'Sin conexión',
};

interface Props {
  compact?: boolean;
}

export default function SyncIndicator({ compact = false }: Props) {
  const [open, setOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const { status, pendingCount, failedItems, lastSyncAt, setFailedItems } = useSyncStore();

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, [open]);

  async function handleSyncNow() {
    setOpen(false);
    await syncAll();
  }

  async function handleRetry(autoId: number) {
    await db.sync_queue.update(autoId, { intentos: 0, ultimo_error: undefined });
    await push();
  }

  async function handleDiscard(item: SyncQueueItem) {
    const ok = window.confirm('Este registro no se sincronizará al servidor. ¿Continuar?');
    if (!ok) return;
    if (item.autoId != null) await db.sync_queue.delete(item.autoId);

    // Cascade: si se descarta un comprobante create, limpiar imputación y adjuntos huérfanos
    if (item.tabla === 'comprobantes' && item.operacion === 'create') {
      const imputacion = await db.imputaciones.where('comprobante_id').equals(item.registro_id).first();
      if (imputacion) {
        await db.sync_queue.where('registro_id').equals(imputacion.id).delete();
      }
      const adjuntosComp = await db.adjuntos.where('comprobante_id').equals(item.registro_id).toArray();
      for (const adj of adjuntosComp) {
        await db.sync_queue.where('registro_id').equals(adj.id).delete();
      }
    }

    // Recargar desde DB para reflejar el cascade
    const newFailed = await db.sync_queue.filter(i => i.intentos >= MAX_RETRIES).toArray();
    setFailedItems(newFailed);
  }

  const showBadge = pendingCount > 0 || status === 'error';

  return (
    <div className="relative" ref={panelRef}>
      <button
        onClick={() => setOpen((v) => !v)}
        title={STATUS_LABEL[status]}
        className={`relative flex items-center gap-2 rounded-lg transition-colors hover:bg-slate-800 ${
          compact ? 'p-2' : 'px-3 py-2.5 w-full'
        } ${STATUS_COLOR[status]}`}
      >
        <SyncIcon status={status} />
        {!compact && (
          <span className="text-sm font-medium">{STATUS_LABEL[status]}</span>
        )}
        {showBadge && (
          <span className={`${compact ? 'absolute -top-1 -right-1' : 'ml-auto'} min-w-[1.1rem] h-[1.1rem] flex items-center justify-center text-[10px] font-bold rounded-full px-1 ${
            status === 'error' ? 'bg-red-500 text-white' : 'bg-amber-500 text-black'
          }`}>
            {status === 'error' ? failedItems.length : pendingCount}
          </span>
        )}
      </button>

      {open && (
        <div className={`absolute bottom-full mb-2 w-72 bg-slate-800 border border-slate-700 rounded-xl shadow-2xl z-50 p-4 text-sm ${compact ? 'right-0' : 'left-0'}`}>
          <div className="flex items-center justify-between mb-3">
            <span className="font-semibold text-white">Sincronización</span>
            <button
              onClick={() => setOpen(false)}
              className="text-slate-400 hover:text-white leading-none"
            >
              ✕
            </button>
          </div>

          <div className={`mb-3 text-xs ${STATUS_COLOR[status]}`}>
            {STATUS_LABEL[status]}
            {lastSyncAt && status !== 'offline' && (
              <span className="text-slate-500"> · {formatRelative(lastSyncAt)}</span>
            )}
          </div>

          {pendingCount > 0 && (
            <p className="text-xs text-amber-400 mb-3">
              {pendingCount} cambio{pendingCount !== 1 ? 's' : ''} pendiente{pendingCount !== 1 ? 's' : ''}
            </p>
          )}

          <button
            onClick={handleSyncNow}
            disabled={status === 'offline' || status === 'syncing'}
            className="w-full py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-medium text-sm transition-colors mb-3"
          >
            {status === 'syncing' ? 'Sincronizando...' : 'Sincronizar ahora'}
          </button>

          {failedItems.length > 0 && (
            <div>
              <p className="text-xs font-medium text-red-400 mb-2">
                Errores ({failedItems.length})
              </p>
              <div className="flex flex-col gap-2 max-h-52 overflow-y-auto pr-1">
                {failedItems.map((item) => (
                  <div key={item.autoId} className="bg-slate-900 rounded-lg p-2.5">
                    <div className="text-xs text-slate-300 mb-1">
                      <span className="text-slate-500">{item.tabla}</span>
                      <span className="text-slate-600 mx-1">·</span>
                      {item.operacion}
                    </div>
                    {item.ultimo_error && (
                      <p className="text-xs text-red-400 truncate mb-1.5" title={item.ultimo_error}>
                        {item.ultimo_error}
                      </p>
                    )}
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => item.autoId != null && handleRetry(item.autoId)}
                        className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
                      >
                        ↩ Reintentar
                      </button>
                      <button
                        onClick={() => handleDiscard(item)}
                        className="text-xs text-slate-500 hover:text-red-400 transition-colors"
                      >
                        Descartar
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
