import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useContactos } from '../hooks/useContactos';

const TIPO_LABEL: Record<string, string> = {
  cliente: 'Cliente',
  proveedor: 'Proveedor',
  ambos: 'Cliente/Prov.',
};

export default function Contactos() {
  const navigate = useNavigate();
  const [busqueda, setBusqueda] = useState('');
  const { contactos, eliminar } = useContactos(busqueda);

  async function handleEliminar(id: string, nombre: string) {
    if (!window.confirm(`¿Eliminar "${nombre}"?`)) return;
    await eliminar(id);
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 pt-5 pb-3">
        <h1 className="text-xl font-bold text-white">Contactos</h1>
        <button
          onClick={() => navigate('/contactos/nuevo')}
          className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium px-3 py-1.5 rounded-lg transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
            <path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
          </svg>
          Nuevo
        </button>
      </div>

      {/* Búsqueda */}
      <div className="px-4 pb-3">
        <input
          type="text"
          placeholder="Buscar por RUC o nombre…"
          value={busqueda}
          onChange={e => setBusqueda(e.target.value)}
          className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
        />
      </div>

      {/* Lista */}
      <div className="flex-1 overflow-y-auto px-4 space-y-2 pb-4">
        {contactos === undefined && (
          <p className="text-slate-400 text-sm py-4">Cargando…</p>
        )}
        {contactos?.length === 0 && (
          <p className="text-slate-400 text-sm py-4">
            {busqueda ? 'Sin resultados.' : 'No hay contactos aún.'}
          </p>
        )}
        {contactos?.map(c => (
          <div
            key={c.id}
            className="bg-slate-800 rounded-lg px-4 py-3 flex items-start justify-between gap-2"
          >
            <button
              className="flex-1 text-left"
              onClick={() => navigate(`/contactos/${c.id}/editar`)}
            >
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm font-medium text-slate-100">{c.razon_social}</span>
                {c.es_frecuente && (
                  <span className="text-xs bg-amber-900/50 text-amber-300 px-1.5 py-0.5 rounded">
                    Frecuente
                  </span>
                )}
              </div>
              <div className="flex items-center gap-3 mt-0.5">
                <span className="text-xs text-slate-400">{c.ruc}</span>
                <span className="text-xs text-slate-500">{TIPO_LABEL[c.tipo] ?? c.tipo}</span>
              </div>
            </button>
            <button
              onClick={() => handleEliminar(c.id, c.razon_social)}
              className="text-slate-600 hover:text-red-400 transition-colors shrink-0 p-1"
              aria-label="Eliminar"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                <path fillRule="evenodd" d="M8.75 1A2.75 2.75 0 006 3.75v.443c-.795.077-1.584.176-2.365.298a.75.75 0 10.23 1.482l.149-.022.841 10.518A2.75 2.75 0 007.596 19h4.807a2.75 2.75 0 002.742-2.53l.841-10.52.149.023a.75.75 0 00.23-1.482A41.03 41.03 0 0014 4.193V3.75A2.75 2.75 0 0011.25 1h-2.5zM10 4c.84 0 1.673.025 2.5.075V3.75c0-.69-.56-1.25-1.25-1.25h-2.5c-.69 0-1.25.56-1.25 1.25v.325C8.327 4.025 9.16 4 10 4zM8.58 7.72a.75.75 0 00-1.5.06l.3 7.5a.75.75 0 101.5-.06l-.3-7.5zm4.34.06a.75.75 0 10-1.5-.06l-.3 7.5a.75.75 0 101.5.06l.3-7.5z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
