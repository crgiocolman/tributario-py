import { useState } from 'react';
import { api } from '../services/api';
import { db } from '../services/db';

// ── Types ────────────────────────────────────────────────────────────────────

type F120Ventas = {
  gravadas_10: number; iva_debito_10: number;
  gravadas_5: number; iva_debito_5: number;
  exentas: number; total_iva_debito: number;
};
type F120Compras = {
  gravadas_10: number; iva_credito_10_utilizado: number;
  gravadas_5: number; iva_credito_5_utilizado: number;
  exentas: number; total_iva_credito_utilizado: number;
};
type F120Liquidacion = {
  iva_debito: number; iva_credito: number;
  saldo: number; a_pagar: number; saldo_a_favor: number;
};
type F120Resumen = {
  periodo: string; ruc: string;
  ventas: F120Ventas; compras: F120Compras; liquidacion: F120Liquidacion;
};

type TramoIRP = { base: number; impuesto: number };
type F515Ingresos = {
  salarios_brutos: number; aporte_ips: number;
  aguinaldo_exonerado: number; honorarios_profesionales: number;
  otros_ingresos: number; total_computable_irp: number;
};
type F515EgresoCategoria = { total: number; cantidad_comprobantes: number };
type F515Liquidacion = {
  tramo_8: TramoIRP; tramo_9: TramoIRP; tramo_10: TramoIRP;
  total_impuesto: number; retenciones_sufridas: number; saldo_a_pagar: number;
};
type F515Resumen = {
  anio_fiscal: number; ruc: string;
  ejercicio_inicio: string; ejercicio_fin: string;
  ingresos: F515Ingresos;
  egresos_deducibles: Record<string, F515EgresoCategoria>;
  total_egresos_deducibles: number;
  renta_neta: number;
  liquidacion_irp: F515Liquidacion;
};

// ── Validation ────────────────────────────────────────────────────────────────

type ValidacionResult = {
  errores: string[];
  warnings: string[];
  totalComprobantes: number;
};

async function validarPeriodo(periodo: string): Promise<ValidacionResult> {
  const comprobantes = await db.comprobantes
    .where('periodo_fiscal').equals(periodo)
    .filter(c => !c.deleted_at)
    .toArray();

  if (comprobantes.length === 0) {
    return { errores: [], warnings: ['Período sin comprobantes — el CSV estará vacío.'], totalComprobantes: 0 };
  }

  const ids = comprobantes.map(c => c.id);
  const imputaciones = await db.imputaciones.where('comprobante_id').anyOf(ids).toArray();
  const imputacionMap = new Set(imputaciones.map(i => i.comprobante_id));

  const errores: string[] = [];
  const warnings: string[] = [];

  for (const c of comprobantes) {
    const suma = c.monto_exento + c.monto_gravado_5 + c.monto_gravado_10;
    if (c.total !== suma) {
      const label = c.numero_comprobante || c.id.slice(0, 8);
      errores.push(`${label}: total ${gs(c.total)} ≠ componentes ${gs(suma)}`);
    }
    if (!imputacionMap.has(c.id)) {
      const label = c.numero_comprobante || c.id.slice(0, 8);
      warnings.push(`${label}: sin imputación (pendiente de sync)`);
    }
  }

  return { errores, warnings, totalComprobantes: comprobantes.length };
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const BASE_URL = '/api/v1';
const gs = (n: number) => `Gs. ${new Intl.NumberFormat('es-PY').format(n)}`;
type CopyState = 'idle' | 'copied';

function getPeriodos(n = 13) {
  const result: { value: string; label: string }[] = [];
  const now = new Date();
  for (let i = 0; i < n; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
    const label = d.toLocaleDateString('es-PY', { year: 'numeric', month: 'long' });
    result.push({ value, label });
  }
  return result;
}

function getAnios(n = 5) {
  const y = new Date().getFullYear();
  return Array.from({ length: n }, (_, i) => y - i);
}

async function downloadCSV(periodo: string) {
  const res = await fetch(`${BASE_URL}/exportar/reg-comprobantes/${periodo}`);
  if (!res.ok) throw new Error(`Error ${res.status}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `reg_comprobantes_${periodo}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

function triggerJSONDownload(data: unknown, filename: string) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function buildTextoF120(r: F120Resumen): string {
  const pad = (label: string, val: string) => `  ${label.padEnd(28)}${val}`;
  return [
    `F120 — ${r.periodo}  (RUC: ${r.ruc})`,
    '',
    'VENTAS',
    pad('Gravadas 10%:', gs(r.ventas.gravadas_10)),
    pad('IVA débito 10%:', gs(r.ventas.iva_debito_10)),
    pad('Gravadas 5%:', gs(r.ventas.gravadas_5)),
    pad('IVA débito 5%:', gs(r.ventas.iva_debito_5)),
    pad('Exentas:', gs(r.ventas.exentas)),
    pad('Total IVA débito:', gs(r.ventas.total_iva_debito)),
    '',
    'COMPRAS',
    pad('Gravadas 10%:', gs(r.compras.gravadas_10)),
    pad('IVA crédito 10%:', gs(r.compras.iva_credito_10_utilizado)),
    pad('Gravadas 5%:', gs(r.compras.gravadas_5)),
    pad('IVA crédito 5%:', gs(r.compras.iva_credito_5_utilizado)),
    pad('Exentas:', gs(r.compras.exentas)),
    pad('Total IVA crédito:', gs(r.compras.total_iva_credito_utilizado)),
    '',
    'LIQUIDACIÓN',
    pad('IVA débito:', gs(r.liquidacion.iva_debito)),
    pad('IVA crédito:', gs(r.liquidacion.iva_credito)),
    pad('Saldo:', gs(r.liquidacion.saldo)),
    pad('A pagar:', gs(r.liquidacion.a_pagar)),
    pad('Saldo a favor:', gs(r.liquidacion.saldo_a_favor)),
  ].join('\n');
}

function buildTextoF515(r: F515Resumen): string {
  const pad = (label: string, val: string) => `  ${label.padEnd(32)}${val}`;
  const egresos = Object.entries(r.egresos_deducibles)
    .map(([cod, e]) => pad(`Cat. ${cod} (${e.cantidad_comprobantes} comp.):`, gs(e.total)))
    .join('\n');
  const { tramo_8: t8, tramo_9: t9, tramo_10: t10 } = r.liquidacion_irp;
  return [
    `F515 — Ejercicio ${r.anio_fiscal}  (RUC: ${r.ruc})`,
    '',
    'INGRESOS',
    pad('Salarios brutos:', gs(r.ingresos.salarios_brutos)),
    pad('Aporte IPS:', gs(r.ingresos.aporte_ips)),
    pad('Aguinaldo exonerado:', gs(r.ingresos.aguinaldo_exonerado)),
    pad('Honorarios profesionales:', gs(r.ingresos.honorarios_profesionales)),
    pad('Otros ingresos:', gs(r.ingresos.otros_ingresos)),
    pad('Total computable IRP:', gs(r.ingresos.total_computable_irp)),
    '',
    'EGRESOS DEDUCIBLES',
    egresos || '  (sin egresos)',
    pad('Total egresos:', gs(r.total_egresos_deducibles)),
    '',
    'LIQUIDACIÓN IRP',
    pad('Renta neta:', gs(r.renta_neta)),
    t8.base > 0 ? pad('Tramo 8% (base):', gs(t8.base)) : '',
    t8.impuesto > 0 ? pad('Impuesto 8%:', gs(t8.impuesto)) : '',
    t9.base > 0 ? pad('Tramo 9% (base):', gs(t9.base)) : '',
    t9.impuesto > 0 ? pad('Impuesto 9%:', gs(t9.impuesto)) : '',
    t10.base > 0 ? pad('Tramo 10% (base):', gs(t10.base)) : '',
    t10.impuesto > 0 ? pad('Impuesto 10%:', gs(t10.impuesto)) : '',
    pad('Total impuesto:', gs(r.liquidacion_irp.total_impuesto)),
    pad('Retenciones sufridas:', gs(r.liquidacion_irp.retenciones_sufridas)),
    pad('Saldo a pagar:', gs(r.liquidacion_irp.saldo_a_pagar)),
  ].filter(l => l !== '').join('\n');
}

// ── Shared sub-components ────────────────────────────────────────────────────

function Row({ label, value, highlight }: { label: string; value: number; highlight?: boolean }) {
  return (
    <div className={`flex justify-between py-1.5 border-b border-slate-700 last:border-0 ${highlight ? 'font-semibold' : ''}`}>
      <span className="text-slate-300 text-sm">{label}</span>
      <span className={`text-sm tabular-nums ${highlight ? 'text-white' : 'text-slate-200'}`}>{gs(value)}</span>
    </div>
  );
}

function SectionBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mt-3">
      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">{title}</p>
      <div>{children}</div>
    </div>
  );
}

function CopyJsonButtons({
  onCopy, onJson, copyState,
}: { onCopy: () => void; onJson: () => void; copyState: CopyState }) {
  return (
    <div className="flex gap-2 mt-4">
      <button onClick={onCopy} className="flex-1 flex items-center justify-center gap-1.5 bg-slate-700 hover:bg-slate-600 text-white text-sm font-medium py-2 rounded-lg transition-colors">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
          <path d="M7 3.5A1.5 1.5 0 0 1 8.5 2h3.879a1.5 1.5 0 0 1 1.06.44l3.122 3.12A1.5 1.5 0 0 1 17 6.622V12.5a1.5 1.5 0 0 1-1.5 1.5h-1v-3.379a3 3 0 0 0-.879-2.121L10.5 5.379A3 3 0 0 0 8.379 4.5H7v-1Z" />
          <path d="M4.5 6A1.5 1.5 0 0 0 3 7.5v9A1.5 1.5 0 0 0 4.5 18h7a1.5 1.5 0 0 0 1.5-1.5v-5.879a1.5 1.5 0 0 0-.44-1.06L9.44 6.439A1.5 1.5 0 0 0 8.378 6H4.5Z" />
        </svg>
        {copyState === 'copied' ? '¡Copiado!' : 'Copiar'}
      </button>
      <button onClick={onJson} className="flex-1 flex items-center justify-center gap-1.5 bg-slate-700 hover:bg-slate-600 text-white text-sm font-medium py-2 rounded-lg transition-colors">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
          <path fillRule="evenodd" d="M10 3a.75.75 0 0 1 .75.75v9.69l2.22-2.22a.75.75 0 1 1 1.06 1.06l-3.5 3.5a.75.75 0 0 1-1.06 0l-3.5-3.5a.75.75 0 1 1 1.06-1.06l2.22 2.22V3.75A.75.75 0 0 1 10 3Z" clipRule="evenodd" />
          <path fillRule="evenodd" d="M3 13.75a.75.75 0 0 1 .75-.75h12.5a.75.75 0 0 1 0 1.5H3.75a.75.75 0 0 1-.75-.75Z" clipRule="evenodd" />
        </svg>
        JSON
      </button>
    </div>
  );
}

// ── F120 Section ─────────────────────────────────────────────────────────────

function F120Section({ periodo }: { periodo: string }) {
  const [data, setData] = useState<F120Resumen | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copyState, setCopyState] = useState<CopyState>('idle');

  async function handleCargar() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<{ data: F120Resumen }>(`/exportar/f120-resumen/${periodo}`);
      setData(res.data);
    } catch {
      setError('Error al cargar. Verificar conexión con el servidor.');
    } finally {
      setLoading(false);
    }
  }

  async function handleCopiar() {
    if (!data) return;
    await navigator.clipboard.writeText(buildTextoF120(data));
    setCopyState('copied');
    setTimeout(() => setCopyState('idle'), 2000);
  }

  return (
    <div className="bg-slate-800 rounded-xl p-4">
      <h2 className="text-white font-semibold mb-1">Resumen F120</h2>
      <p className="text-slate-400 text-xs mb-3">Liquidación IVA para llenar en Marangatu</p>
      <button onClick={handleCargar} disabled={loading}
        className="w-full flex items-center justify-center gap-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white font-medium py-2 rounded-lg transition-colors text-sm">
        {loading ? 'Cargando...' : data ? 'Actualizar' : 'Ver resumen'}
      </button>
      {error && <p className="text-red-400 text-sm mt-2">{error}</p>}
      {data && (
        <>
          <SectionBlock title="Ventas">
            <Row label="Gravadas 10%" value={data.ventas.gravadas_10} />
            <Row label="IVA débito 10%" value={data.ventas.iva_debito_10} />
            <Row label="Gravadas 5%" value={data.ventas.gravadas_5} />
            <Row label="IVA débito 5%" value={data.ventas.iva_debito_5} />
            <Row label="Exentas" value={data.ventas.exentas} />
            <Row label="Total IVA débito" value={data.ventas.total_iva_debito} highlight />
          </SectionBlock>
          <SectionBlock title="Compras">
            <Row label="Gravadas 10%" value={data.compras.gravadas_10} />
            <Row label="IVA crédito 10%" value={data.compras.iva_credito_10_utilizado} />
            <Row label="Gravadas 5%" value={data.compras.gravadas_5} />
            <Row label="IVA crédito 5%" value={data.compras.iva_credito_5_utilizado} />
            <Row label="Exentas" value={data.compras.exentas} />
            <Row label="Total IVA crédito" value={data.compras.total_iva_credito_utilizado} highlight />
          </SectionBlock>
          <SectionBlock title="Liquidación">
            <Row label="IVA débito" value={data.liquidacion.iva_debito} />
            <Row label="IVA crédito" value={data.liquidacion.iva_credito} />
            <Row label="Saldo" value={data.liquidacion.saldo} />
            <Row label="A pagar" value={data.liquidacion.a_pagar} highlight />
            <Row label="Saldo a favor" value={data.liquidacion.saldo_a_favor} />
          </SectionBlock>
          <CopyJsonButtons
            onCopy={handleCopiar}
            onJson={() => triggerJSONDownload(data, `f120_${data.periodo}.json`)}
            copyState={copyState}
          />
        </>
      )}
    </div>
  );
}

// ── F515 Section ─────────────────────────────────────────────────────────────

function F515Section() {
  const anios = getAnios();
  const [anio, setAnio] = useState(anios[0]);
  const [data, setData] = useState<F515Resumen | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copyState, setCopyState] = useState<CopyState>('idle');

  async function handleCargar() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<{ data: F515Resumen }>(`/exportar/f515-resumen/${anio}`);
      setData(res.data);
    } catch {
      setError('Error al cargar. Verificar conexión con el servidor.');
    } finally {
      setLoading(false);
    }
  }

  async function handleCopiar() {
    if (!data) return;
    await navigator.clipboard.writeText(buildTextoF515(data));
    setCopyState('copied');
    setTimeout(() => setCopyState('idle'), 2000);
  }

  const { tramo_8: t8, tramo_9: t9, tramo_10: t10 } = data?.liquidacion_irp ?? {
    tramo_8: { base: 0, impuesto: 0 },
    tramo_9: { base: 0, impuesto: 0 },
    tramo_10: { base: 0, impuesto: 0 },
  };

  return (
    <div className="bg-slate-800 rounded-xl p-4">
      <h2 className="text-white font-semibold mb-1">Resumen F515</h2>
      <p className="text-slate-400 text-xs mb-3">Consolidación anual IRP-RSP</p>

      <div className="flex gap-2 mb-3">
        <select
          value={anio}
          onChange={e => { setAnio(Number(e.target.value)); setData(null); }}
          className="flex-1 bg-slate-700 text-white rounded-lg px-3 py-2 text-sm border border-slate-600 focus:outline-none focus:border-blue-500"
        >
          {anios.map(y => <option key={y} value={y} className="bg-slate-800">{y}</option>)}
        </select>
        <button onClick={handleCargar} disabled={loading}
          className="flex-1 flex items-center justify-center bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white font-medium py-2 rounded-lg transition-colors text-sm">
          {loading ? 'Cargando...' : data ? 'Actualizar' : 'Ver resumen'}
        </button>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      {data && (
        <>
          <SectionBlock title="Ingresos">
            <Row label="Salarios brutos" value={data.ingresos.salarios_brutos} />
            <Row label="Aporte IPS (deducible)" value={data.ingresos.aporte_ips} />
            <Row label="Aguinaldo exonerado" value={data.ingresos.aguinaldo_exonerado} />
            <Row label="Honorarios profesionales" value={data.ingresos.honorarios_profesionales} />
            <Row label="Otros ingresos" value={data.ingresos.otros_ingresos} />
            <Row label="Total computable IRP" value={data.ingresos.total_computable_irp} highlight />
          </SectionBlock>

          <SectionBlock title="Egresos deducibles por categoría">
            {Object.keys(data.egresos_deducibles).length === 0
              ? <p className="text-slate-500 text-sm py-1">Sin egresos registrados</p>
              : Object.entries(data.egresos_deducibles).map(([cod, e]) => (
                <div key={cod} className="flex justify-between py-1.5 border-b border-slate-700 last:border-0">
                  <span className="text-slate-300 text-sm">
                    Cat. <span className="font-mono">{cod}</span>
                    <span className="text-slate-500 ml-1">({e.cantidad_comprobantes} comp.)</span>
                  </span>
                  <span className="text-slate-200 text-sm tabular-nums">{gs(e.total)}</span>
                </div>
              ))
            }
            <Row label="Total egresos" value={data.total_egresos_deducibles} highlight />
          </SectionBlock>

          <SectionBlock title="Liquidación IRP">
            <Row label="Renta neta" value={data.renta_neta} highlight />
            {t8.base > 0 && <Row label="Base tramo 8%" value={t8.base} />}
            {t8.impuesto > 0 && <Row label="Impuesto 8%" value={t8.impuesto} />}
            {t9.base > 0 && <Row label="Base tramo 9%" value={t9.base} />}
            {t9.impuesto > 0 && <Row label="Impuesto 9%" value={t9.impuesto} />}
            {t10.base > 0 && <Row label="Base tramo 10%" value={t10.base} />}
            {t10.impuesto > 0 && <Row label="Impuesto 10%" value={t10.impuesto} />}
            <Row label="Total impuesto" value={data.liquidacion_irp.total_impuesto} highlight />
            <Row label="Retenciones sufridas" value={data.liquidacion_irp.retenciones_sufridas} />
            <Row label="Saldo a pagar" value={data.liquidacion_irp.saldo_a_pagar} highlight />
          </SectionBlock>

          <CopyJsonButtons
            onCopy={handleCopiar}
            onJson={() => triggerJSONDownload(data, `f515_${data.anio_fiscal}.json`)}
            copyState={copyState}
          />
        </>
      )}
    </div>
  );
}

// ── Backup Section ───────────────────────────────────────────────────────────

function BackupSection() {
  const anios = getAnios();
  const [anio, setAnio] = useState(anios[0]);
  const [rangoCustom, setRangoCustom] = useState(false);
  const [desde, setDesde] = useState('');
  const [hasta, setHasta] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDescargar() {
    setLoading(true);
    setError(null);
    try {
      let url = `${BASE_URL}/exportar/backup-adjuntos?anio=${anio}`;
      if (rangoCustom && desde) url += `&desde=${desde}`;
      if (rangoCustom && hasta) url += `&hasta=${hasta}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Error ${res.status}`);
      const blob = await res.blob();
      const objectUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = objectUrl;
      a.download = `adjuntos_${anio}.zip`;
      a.click();
      URL.revokeObjectURL(objectUrl);
    } catch {
      setError('Error al generar el backup. Verificar conexión con el servidor.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-slate-800 rounded-xl p-4">
      <h2 className="text-white font-semibold mb-1">Backup adjuntos</h2>
      <p className="text-slate-400 text-xs mb-3">ZIP con fotos y PDFs del ejercicio</p>
      <div className="space-y-3">
        <select
          value={anio}
          onChange={e => setAnio(Number(e.target.value))}
          className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 text-sm border border-slate-600 focus:outline-none focus:border-blue-500"
        >
          {anios.map(y => <option key={y} value={y} className="bg-slate-800">{y}</option>)}
        </select>

        <label className="flex items-center gap-2 text-slate-300 text-sm cursor-pointer select-none">
          <input
            type="checkbox"
            checked={rangoCustom}
            onChange={e => setRangoCustom(e.target.checked)}
            className="accent-blue-500"
          />
          Rango personalizado
        </label>

        {rangoCustom && (
          <div className="flex gap-2">
            <input
              type="date"
              value={desde}
              onChange={e => setDesde(e.target.value)}
              className="flex-1 bg-slate-700 text-white text-sm rounded-lg px-3 py-2 border border-slate-600 focus:outline-none focus:border-blue-500"
            />
            <input
              type="date"
              value={hasta}
              onChange={e => setHasta(e.target.value)}
              className="flex-1 bg-slate-700 text-white text-sm rounded-lg px-3 py-2 border border-slate-600 focus:outline-none focus:border-blue-500"
            />
          </div>
        )}

        <button
          onClick={handleDescargar}
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white font-medium py-2 rounded-lg transition-colors text-sm"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
            <path d="M10.75 2.75a.75.75 0 0 0-1.5 0v8.614L6.295 8.235a.75.75 0 1 0-1.09 1.03l4.25 4.5a.75.75 0 0 0 1.09 0l4.25-4.5a.75.75 0 0 0-1.09-1.03l-2.955 3.129V2.75Z" />
            <path d="M3.5 12.75a.75.75 0 0 0-1.5 0v2.5A2.75 2.75 0 0 0 4.75 18h10.5A2.75 2.75 0 0 0 18 15.25v-2.5a.75.75 0 0 0-1.5 0v2.5c0 .69-.56 1.25-1.25 1.25H4.75c-.69 0-1.25-.56-1.25-1.25v-2.5Z" />
          </svg>
          {loading ? 'Generando ZIP...' : 'Descargar ZIP'}
        </button>
        {error && <p className="text-red-400 text-sm">{error}</p>}
      </div>
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function Reportes() {
  const periodos = getPeriodos();
  const [periodo, setPeriodo] = useState(periodos[0].value);
  const [csvLoading, setCsvLoading] = useState(false);
  const [csvError, setCsvError] = useState<string | null>(null);
  const [validacion, setValidacion] = useState<ValidacionResult | null>(null);

  function handlePeriodoChange(p: string) {
    setPeriodo(p);
    setValidacion(null);
  }

  async function handleExportarCSV() {
    setCsvLoading(true);
    setCsvError(null);
    setValidacion(null);
    try {
      const result = await validarPeriodo(periodo);
      if (result.errores.length > 0 || result.warnings.length > 0) {
        setValidacion(result);
        return;
      }
      await downloadCSV(periodo);
    } catch {
      setCsvError('Error al exportar. Verificar conexión con el servidor.');
    } finally {
      setCsvLoading(false);
    }
  }

  async function handleExportarDeTodasFormas() {
    setCsvLoading(true);
    setCsvError(null);
    try {
      await downloadCSV(periodo);
      setValidacion(null);
    } catch {
      setCsvError('Error al exportar. Verificar conexión con el servidor.');
    } finally {
      setCsvLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 pt-5 pb-3">
        <h1 className="text-xl font-bold text-white">Reportes</h1>
      </div>
      <div className="flex-1 overflow-y-auto px-4 space-y-4 pb-6">

        {/* Selector de período compartido (4.1 y 4.2) */}
        <div className="bg-slate-700 rounded-lg px-3 py-2 flex items-center gap-3">
          <span className="text-slate-300 text-sm whitespace-nowrap">Período</span>
          <select
            value={periodo}
            onChange={e => handlePeriodoChange(e.target.value)}
            className="flex-1 bg-transparent text-white text-sm focus:outline-none"
          >
            {periodos.map(p => (
              <option key={p.value} value={p.value} className="bg-slate-800">{p.label}</option>
            ))}
          </select>
        </div>

        {/* 4.1 — CSV Reg. Comprobantes */}
        <div className="bg-slate-800 rounded-xl p-4">
          <h2 className="text-white font-semibold mb-1">Reg. Comprobantes (IVA)</h2>
          <p className="text-slate-400 text-xs mb-3">CSV para importar en Marangatu</p>
          <button onClick={handleExportarCSV} disabled={csvLoading}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium py-2 rounded-lg transition-colors text-sm">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
              <path fillRule="evenodd" d="M10 3a.75.75 0 0 1 .75.75v9.69l2.22-2.22a.75.75 0 1 1 1.06 1.06l-3.5 3.5a.75.75 0 0 1-1.06 0l-3.5-3.5a.75.75 0 1 1 1.06-1.06l2.22 2.22V3.75A.75.75 0 0 1 10 3Z" clipRule="evenodd" />
              <path fillRule="evenodd" d="M3 13.75a.75.75 0 0 1 .75-.75h12.5a.75.75 0 0 1 0 1.5H3.75a.75.75 0 0 1-.75-.75Z" clipRule="evenodd" />
            </svg>
            {csvLoading ? 'Validando...' : 'Exportar CSV'}
          </button>
          {csvError && <p className="text-red-400 text-sm mt-2">{csvError}</p>}

          {/* Panel de validación (4.4) */}
          {validacion && (
            <div className="mt-3 space-y-2">
              {validacion.errores.length > 0 && (
                <div className="bg-red-900/30 border border-red-700 rounded-lg p-3">
                  <p className="text-red-400 text-xs font-semibold mb-1">
                    {validacion.errores.length} error{validacion.errores.length > 1 ? 'es' : ''} — corregir antes de exportar
                  </p>
                  <ul className="space-y-0.5">
                    {validacion.errores.map((e, i) => (
                      <li key={i} className="text-red-300 text-xs">• {e}</li>
                    ))}
                  </ul>
                </div>
              )}
              {validacion.warnings.length > 0 && (
                <div className="bg-yellow-900/30 border border-yellow-700 rounded-lg p-3">
                  <p className="text-yellow-400 text-xs font-semibold mb-1">
                    {validacion.warnings.length} advertencia{validacion.warnings.length > 1 ? 's' : ''}
                  </p>
                  <ul className="space-y-0.5">
                    {validacion.warnings.map((w, i) => (
                      <li key={i} className="text-yellow-300 text-xs">• {w}</li>
                    ))}
                  </ul>
                </div>
              )}
              {validacion.errores.length === 0 && (
                <button onClick={handleExportarDeTodasFormas} disabled={csvLoading}
                  className="w-full bg-yellow-700 hover:bg-yellow-600 disabled:opacity-50 text-white text-sm font-medium py-2 rounded-lg transition-colors">
                  Exportar de todas formas
                </button>
              )}
            </div>
          )}
        </div>

        {/* 4.2 — Resumen F120 */}
        <F120Section periodo={periodo} />

        {/* 4.3 — Resumen F515 */}
        <F515Section />

        {/* 4.5 — Backup adjuntos */}
        <BackupSection />

      </div>
    </div>
  );
}
