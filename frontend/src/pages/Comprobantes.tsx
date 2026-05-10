import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useComprobantes } from '../hooks/useComprobantes';

const TIPO_OP_LABEL: Record<string, string> = { compra: 'Compra', venta: 'Venta' };
const TIPO_COMP_LABEL: Record<string, string> = {
  factura: 'Factura',
  autofactura: 'Autofactura',
  ticket: 'Ticket',
  nota_credito: 'N. Crédito',
  nota_debito: 'N. Débito',
  boleta_resimple: 'Boleta',
  liquidacion_salario: 'Liq. Salario',
};

const formatGs = (n: number) => new Intl.NumberFormat('es-PY').format(n);

function getUltimosPeridos(n = 13) {
  const result: { value: string; label: string }[] = [{ value: '', label: 'Todos los períodos' }];
  const now = new Date();
  for (let i = 0; i < n; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
    const label = d.toLocaleDateString('es-PY', { year: 'numeric', month: 'long' });
    result.push({ value, label });
  }
  return result;
}

export default function Comprobantes() {
  const navigate = useNavigate();
  const [periodo, setPeriodo] = useState('');
  const [tipoOp, setTipoOp] = useState('');
  const { comprobantes, eliminar } = useComprobantes({ periodo_fiscal: periodo || undefined, tipo_operacion: tipoOp || undefined });
  const cameraInputRef = useRef<HTMLInputElement>(null);

  function handleCameraCapture(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = '';
    navigate('/comprobantes/nuevo', { state: { pendingFile: file } });
  }

  async function handleEliminar(id: string, num: string) {
    if (!window.confirm(`¿Eliminar comprobante "${num}"?`)) return;
    await eliminar(id);
  }

  const periodos = getUltimosPeridos();

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 pt-5 pb-3">
        <h1 className="text-xl font-bold text-white">Comprobantes</h1>
        <button
          onClick={() => navigate('/comprobantes/nuevo')}
          className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium px-3 py-1.5 rounded-lg transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
            <path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
          </svg>
          Nuevo
        </button>
      </div>

      {/* Filtros */}
      <div className="px-4 pb-3 flex gap-2">
        <select
          value={periodo}
          onChange={e => setPeriodo(e.target.value)}
          className="flex-1 rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
        >
          {periodos.map(p => (
            <option key={p.value} value={p.value}>{p.label}</option>
          ))}
        </select>
        <select
          value={tipoOp}
          onChange={e => setTipoOp(e.target.value)}
          className="rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
        >
          <option value="">Todos</option>
          <option value="compra">Compras</option>
          <option value="venta">Ventas</option>
        </select>
      </div>

      {/* Lista */}
      <div className="flex-1 overflow-y-auto px-4 space-y-2 pb-4">
        {comprobantes === undefined && (
          <p className="text-slate-400 text-sm py-4">Cargando…</p>
        )}
        {comprobantes?.length === 0 && (
          <p className="text-slate-400 text-sm py-4">No hay comprobantes para los filtros seleccionados.</p>
        )}
        {comprobantes?.map(c => (
          <div
            key={c.id}
            className="bg-slate-800 rounded-lg px-4 py-3 flex items-start justify-between gap-2"
          >
            <button
              className="flex-1 text-left"
              onClick={() => navigate(`/comprobantes/${c.id}/editar`)}
            >
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${c.tipo_operacion === 'compra' ? 'bg-purple-900/50 text-purple-300' : 'bg-green-900/50 text-green-300'}`}>
                  {TIPO_OP_LABEL[c.tipo_operacion]}
                </span>
                <span className="text-xs text-slate-400">{TIPO_COMP_LABEL[c.tipo_comprobante] ?? c.tipo_comprobante}</span>
                {c.numero_comprobante && (
                  <span className="text-xs text-slate-500">#{c.numero_comprobante}</span>
                )}
              </div>
              <div className="flex items-center gap-3 mt-1">
                <span className="text-sm font-semibold text-slate-100">{formatGs(c.total)} Gs</span>
                <span className="text-xs text-slate-400">{c.fecha_emision}</span>
                <span className="text-xs text-slate-500">{c.periodo_fiscal}</span>
              </div>
            </button>
            <button
              onClick={() => handleEliminar(c.id, c.numero_comprobante ?? c.id.slice(0, 8))}
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

      {/* Hidden camera input */}
      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="sr-only"
        onChange={handleCameraCapture}
      />

      {/* Camera FAB */}
      <button
        onClick={() => cameraInputRef.current?.click()}
        className="fixed bottom-20 right-4 w-14 h-14 bg-blue-600 hover:bg-blue-500 rounded-full shadow-lg flex items-center justify-center z-10 transition-colors"
        aria-label="Capturar foto de comprobante"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6">
          <path d="M12 9a3.75 3.75 0 100 7.5A3.75 3.75 0 0012 9z" />
          <path fillRule="evenodd" d="M9.344 3.071a49.52 49.52 0 015.312 0c.967.052 1.83.585 2.332 1.39l.821 1.317c.24.383.645.643 1.11.71.386.054.77.113 1.152.177 1.432.239 2.429 1.493 2.429 2.909V18a3 3 0 01-3 3h-15a3 3 0 01-3-3V9.574c0-1.416.997-2.67 2.429-2.909.382-.064.766-.123 1.151-.178a1.56 1.56 0 001.11-.71l.822-1.315a2.942 2.942 0 012.332-1.39zM6.75 12.75a5.25 5.25 0 1110.5 0 5.25 5.25 0 01-10.5 0zM12 10.5a2.25 2.25 0 100 4.5 2.25 2.25 0 000-4.5z" clipRule="evenodd" />
        </svg>
      </button>
    </div>
  );
}
