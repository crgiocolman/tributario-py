import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { useDashboard } from '../hooks/useDashboard';

const formatGs = (n: number) => new Intl.NumberFormat('es-PY').format(n);
const formatGsCompact = (n: number) => {
  const abs = Math.abs(n);
  if (abs >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return String(n);
};

const PIE_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316'];

function AlertaVencimiento({ tipo, fecha, dias }: { tipo: string; fecha: string; dias: number }) {
  const urgente = dias <= 7;
  const dateStr = new Date(fecha + 'T12:00:00').toLocaleDateString('es-PY', { day: 'numeric', month: 'long' });
  return (
    <div className={`rounded-xl px-4 py-3 border flex items-center justify-between ${urgente ? 'bg-red-900/30 border-red-700' : 'bg-amber-900/20 border-amber-700/60'}`}>
      <div>
        <p className={`text-sm font-semibold ${urgente ? 'text-red-300' : 'text-amber-300'}`}>{tipo}</p>
        <p className="text-xs text-slate-400 mt-0.5">Vence el {dateStr}</p>
      </div>
      <span className={`text-sm font-bold px-2.5 py-1 rounded-lg ${urgente ? 'bg-red-800 text-red-200' : 'bg-amber-800/50 text-amber-200'}`}>
        {dias === 0 ? 'Hoy' : `${dias}d`}
      </span>
    </div>
  );
}

export default function Home() {
  const data = useDashboard();

  if (!data) {
    return (
      <div className="flex items-center justify-center h-full">
        <span className="text-slate-400 text-sm">Cargando…</span>
      </div>
    );
  }

  const {
    periodoActual,
    cantidadComprobantes,
    ivaDebito,
    ivaCredito,
    saldoIva,
    anioActual,
    ivaAnual,
    egresosPorCategoria,
    ingresosComputables,
    egresosDeducibles,
    rentaNeta,
    impuestoEstimado,
    proximosVencimientos,
  } = data;

  const mesNombre = new Date(periodoActual + '-15').toLocaleDateString('es-PY', {
    month: 'long',
    year: 'numeric',
  });

  return (
    <div className="p-4 space-y-5 pb-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Inicio</h1>
        <p className="text-sm text-slate-400 capitalize mt-0.5">{mesNombre}</p>
      </div>

      {/* Alertas de vencimiento */}
      {proximosVencimientos.length > 0 && (
        <div className="space-y-2">
          {proximosVencimientos.map(v => (
            <AlertaVencimiento key={v.tipo} tipo={v.tipo} fecha={v.fecha} dias={v.diasRestantes} />
          ))}
        </div>
      )}

      {/* Resumen del mes */}
      <section>
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3">
          Resumen {mesNombre}
        </h2>
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-slate-800 rounded-xl p-3">
            <p className="text-xs text-slate-400 mb-1">Comprobantes</p>
            <p className="text-2xl font-bold text-white">{cantidadComprobantes}</p>
          </div>
          <div className="bg-slate-800 rounded-xl p-3">
            <p className="text-xs text-slate-400 mb-1">Saldo IVA</p>
            <p className={`text-xl font-bold ${saldoIva >= 0 ? 'text-amber-300' : 'text-green-400'}`}>
              {formatGsCompact(Math.abs(saldoIva))}
            </p>
            <p className="text-xs text-slate-500 mt-0.5">{saldoIva >= 0 ? 'a pagar' : 'a favor'}</p>
          </div>
          <div className="bg-slate-800 rounded-xl p-3">
            <p className="text-xs text-slate-400 mb-1">IVA débito</p>
            <p className="text-xl font-bold text-amber-300">{formatGsCompact(ivaDebito)}</p>
          </div>
          <div className="bg-slate-800 rounded-xl p-3">
            <p className="text-xs text-slate-400 mb-1">IVA crédito</p>
            <p className="text-xl font-bold text-blue-300">{formatGsCompact(ivaCredito)}</p>
          </div>
        </div>
      </section>

      {/* IVA mensual (gráfico de barras) */}
      <section>
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3">
          IVA mensual {anioActual}
        </h2>
        <div className="bg-slate-800 rounded-xl p-3 pt-4">
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={ivaAnual} margin={{ top: 0, right: 4, left: -16, bottom: 0 }}>
              <XAxis
                dataKey="mes"
                tick={{ fill: '#64748b', fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tickFormatter={formatGsCompact}
                tick={{ fill: '#64748b', fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                formatter={(value) => [formatGs(Number(value)) + ' Gs']}
                contentStyle={{
                  background: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: 8,
                  fontSize: 12,
                }}
                labelStyle={{ color: '#cbd5e1' }}
              />
              <Bar dataKey="debito" name="IVA Débito" fill="#f59e0b" radius={[3, 3, 0, 0]} maxBarSize={18} />
              <Bar dataKey="credito" name="IVA Crédito" fill="#60a5fa" radius={[3, 3, 0, 0]} maxBarSize={18} />
            </BarChart>
          </ResponsiveContainer>
          <div className="flex gap-5 justify-center mt-3">
            <span className="flex items-center gap-1.5 text-xs text-slate-400">
              <span className="w-2.5 h-2.5 rounded-sm bg-amber-400 inline-block" />
              IVA Débito
            </span>
            <span className="flex items-center gap-1.5 text-xs text-slate-400">
              <span className="w-2.5 h-2.5 rounded-sm bg-blue-400 inline-block" />
              IVA Crédito
            </span>
          </div>
        </div>
      </section>

      {/* Egresos por categoría IRP (gráfico circular) */}
      {egresosPorCategoria.length > 0 && (
        <section>
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3">
            Egresos por categoría {anioActual}
          </h2>
          <div className="bg-slate-800 rounded-xl p-3">
            <ResponsiveContainer width="100%" height={170}>
              <PieChart>
                <Pie
                  data={egresosPorCategoria}
                  dataKey="valor"
                  nameKey="nombre"
                  cx="50%"
                  cy="50%"
                  outerRadius={72}
                  innerRadius={34}
                  paddingAngle={2}
                >
                  {egresosPorCategoria.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value) => [formatGs(Number(value)) + ' Gs']}
                  contentStyle={{
                    background: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="mt-2 space-y-2">
              {egresosPorCategoria.map((cat, i) => (
                <div key={cat.nombre} className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-2 min-w-0">
                    <span
                      className="w-2.5 h-2.5 rounded-sm shrink-0"
                      style={{ background: PIE_COLORS[i % PIE_COLORS.length] }}
                    />
                    <span className="text-slate-300 truncate">{cat.nombre}</span>
                  </span>
                  <span className="text-slate-400 ml-2 shrink-0">{formatGs(cat.valor)} Gs</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Proyección IRP anual */}
      <section>
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3">
          Proyección IRP {anioActual}
        </h2>
        <div className="bg-slate-800 rounded-xl p-4 space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-slate-400">Ingresos computables</span>
            <span className="text-green-300 font-medium">{formatGs(ingresosComputables)} Gs</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-slate-400">Egresos deducibles</span>
            <span className="text-blue-300 font-medium">{formatGs(egresosDeducibles)} Gs</span>
          </div>
          <div className="border-t border-slate-700 pt-3 flex justify-between text-sm">
            <span className="text-slate-300 font-medium">Renta neta estimada</span>
            <span className="text-white font-bold">{formatGs(rentaNeta)} Gs</span>
          </div>
          {rentaNeta >= 80_000_000 && (
            <div className="bg-amber-900/30 border border-amber-700/50 rounded-lg px-3 py-2 text-xs text-amber-300">
              Supera umbral IRP (80.000.000 Gs) — Declaración F515 obligatoria
            </div>
          )}
          <div className="flex justify-between items-center pt-1">
            <span className="text-sm text-slate-300 font-medium">Impuesto estimado</span>
            <span className={`text-lg font-bold ${impuestoEstimado > 0 ? 'text-red-300' : 'text-slate-500'}`}>
              {formatGs(impuestoEstimado)} Gs
            </span>
          </div>
        </div>
      </section>
    </div>
  );
}
