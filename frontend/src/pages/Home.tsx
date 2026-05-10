import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { db } from '../services/db';

type ApiStatus = 'checking' | 'ok' | 'error';
type DbStatus = 'checking' | 'ok' | 'error';

export default function Home() {
  const [apiStatus, setApiStatus] = useState<ApiStatus>('checking');
  const [dbStatus, setDbStatus] = useState<DbStatus>('checking');

  useEffect(() => {
    api.get('/categorias-irp')
      .then(() => setApiStatus('ok'))
      .catch(() => setApiStatus('error'));
  }, []);

  useEffect(() => {
    db.open()
      .then(() => setDbStatus('ok'))
      .catch(() => setDbStatus('error'));
  }, []);

  const statusBadge = (status: ApiStatus | DbStatus, labels: Record<string, string>) => {
    const colors: Record<string, string> = {
      checking: 'bg-slate-700 text-slate-300',
      ok: 'bg-green-900 text-green-300',
      error: 'bg-red-900 text-red-300',
    };
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[status]}`}>
        {labels[status]}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col items-center justify-center p-4">
      <h1 className="text-3xl font-bold text-white mb-8">TributarioPY</h1>

      <div className="w-full max-w-sm space-y-3">
        <div className="flex items-center justify-between bg-slate-800 rounded-lg px-4 py-3">
          <span className="text-sm text-slate-300">Backend API</span>
          {statusBadge(apiStatus, { checking: 'Verificando…', ok: 'Conectado', error: 'Sin conexión' })}
        </div>

        <div className="flex items-center justify-between bg-slate-800 rounded-lg px-4 py-3">
          <span className="text-sm text-slate-300">IndexedDB</span>
          {statusBadge(dbStatus, { checking: 'Inicializando…', ok: 'OK', error: 'Error' })}
        </div>
      </div>
    </div>
  );
}
