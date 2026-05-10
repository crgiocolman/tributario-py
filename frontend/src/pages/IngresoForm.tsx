import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { db, type ContactoLocal } from '../services/db';
import { useIngresos } from '../hooks/useIngresos';

interface FormState {
  tipo_ingreso: 'salario' | 'aguinaldo' | 'vacaciones' | 'liquidacion_final' | 'honorarios' | 'otros';
  periodo_devengado: string;
  fecha_percepcion: string;
  monto_bruto: string;
  aporte_ips_trabajador: string;
  otros_descuentos: string;
  monto_exonerado: string;
  notas: string;
}

const INITIAL: FormState = {
  tipo_ingreso: 'salario',
  periodo_devengado: new Date().toISOString().slice(0, 7),
  fecha_percepcion: new Date().toISOString().slice(0, 10),
  monto_bruto: '0',
  aporte_ips_trabajador: '0',
  otros_descuentos: '0',
  monto_exonerado: '0',
  notas: '',
};

const inputCls = 'w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500';
const labelCls = 'block text-xs font-medium text-slate-400 mb-1';
const readonlyCls = 'w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-sm text-slate-300';

const toInt = (s: string) => Math.max(0, Math.round(Number(s) || 0));
const formatGs = (n: number) => new Intl.NumberFormat('es-PY').format(n);

const ES_GRAVADO: Record<string, boolean> = {
  salario: true,
  honorarios: true,
  otros: true,
  vacaciones: true,
  liquidacion_final: true,
  aguinaldo: false,
};

export default function IngresoForm() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { crear, actualizar, calcularAcumuladoAnual } = useIngresos();
  const esEdicion = Boolean(id);

  const [form, setForm] = useState<FormState>(INITIAL);
  const [contactoQuery, setContactoQuery] = useState('');
  const [contactoSeleccionado, setContactoSeleccionado] = useState<ContactoLocal | null>(null);
  const [sugerencias, setSugerencias] = useState<ContactoLocal[]>([]);
  const [mostrarDropdown, setMostrarDropdown] = useState(false);
  const [acumulado, setAcumulado] = useState(0);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState('');
  const [ipsManual, setIpsManual] = useState(false);

  // Derivados
  const bruto = toInt(form.monto_bruto);
  const ips = toInt(form.aporte_ips_trabajador);
  const otros = toInt(form.otros_descuentos);
  const exonerado = toInt(form.monto_exonerado);
  const computable = Math.max(0, bruto - ips - otros - exonerado);
  const anio = parseInt(form.periodo_devengado.slice(0, 4)) || 0;

  // Auto-calcular IPS al cambiar monto bruto (si no fue tocado manualmente)
  useEffect(() => {
    if (!ipsManual) {
      setForm(p => ({ ...p, aporte_ips_trabajador: String(Math.round(bruto * 0.09)) }));
    }
  }, [bruto, ipsManual]);

  // Acumulado anual en tiempo real
  useEffect(() => {
    if (!anio) return;
    calcularAcumuladoAnual(anio, id).then(prev => setAcumulado(prev + computable));
  }, [anio, computable, id]);

  // Cargar datos en modo edición
  useEffect(() => {
    if (!id) return;
    db.ingresos.get(id).then(async i => {
      if (!i) return;
      setForm({
        tipo_ingreso: i.tipo_ingreso,
        periodo_devengado: i.periodo_devengado,
        fecha_percepcion: i.fecha_percepcion,
        monto_bruto: String(i.monto_bruto),
        aporte_ips_trabajador: String(i.aporte_ips_trabajador),
        otros_descuentos: String(i.otros_descuentos),
        monto_exonerado: String(i.monto_exonerado),
        notas: i.notas ?? '',
      });
      setIpsManual(true);
      const contacto = await db.contactos.get(i.contacto_id);
      if (contacto) {
        setContactoSeleccionado(contacto);
        setContactoQuery(contacto.razon_social);
      }
    });
  }, [id]);

  // Autocomplete contacto
  useEffect(() => {
    if (!contactoQuery.trim() || contactoSeleccionado) {
      setSugerencias([]);
      return;
    }
    const q = contactoQuery.toLowerCase();
    db.contactos
      .filter(c => !c.deleted_at && (c.ruc.includes(q) || c.razon_social.toLowerCase().includes(q)))
      .limit(8)
      .toArray()
      .then(setSugerencias);
  }, [contactoQuery, contactoSeleccionado]);

  function seleccionarContacto(c: ContactoLocal) {
    setContactoSeleccionado(c);
    setContactoQuery(c.razon_social);
    setSugerencias([]);
    setMostrarDropdown(false);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!contactoSeleccionado) {
      setError('Seleccioná un empleador/contacto.');
      return;
    }
    if (!form.periodo_devengado || !form.fecha_percepcion) {
      setError('El período y la fecha de percepción son obligatorios.');
      return;
    }
    setError('');
    setGuardando(true);

    try {
      const datos = {
        contacto_id: contactoSeleccionado.id,
        tipo_ingreso: form.tipo_ingreso,
        periodo_devengado: form.periodo_devengado,
        fecha_percepcion: form.fecha_percepcion,
        monto_bruto: bruto,
        aporte_ips_trabajador: ips,
        otros_descuentos: otros,
        monto_exonerado: exonerado,
        monto_computable_irp: computable,
        es_gravado_irp: ES_GRAVADO[form.tipo_ingreso] ?? true,
        notas: form.notas.trim() || undefined,
      };

      if (esEdicion && id) {
        await actualizar(id, datos);
      } else {
        await crear(datos);
      }
      navigate('/ingresos');
    } catch (err) {
      setError('Error al guardar. Intentá de nuevo.');
      console.error(err);
    } finally {
      setGuardando(false);
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="sticky top-0 z-10 bg-slate-950 flex items-center gap-3 px-4 pt-5 pb-4 border-b border-slate-800">
        <button onClick={() => navigate('/ingresos')} className="text-slate-400 hover:text-slate-200 transition-colors">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
            <path fillRule="evenodd" d="M17 10a.75.75 0 01-.75.75H5.612l4.158 3.96a.75.75 0 11-1.04 1.08l-5.5-5.25a.75.75 0 010-1.08l5.5-5.25a.75.75 0 111.04 1.08L5.612 9.25H16.25A.75.75 0 0117 10z" clipRule="evenodd" />
          </svg>
        </button>
        <h1 className="text-lg font-bold text-white">
          {esEdicion ? 'Editar ingreso' : 'Nuevo ingreso'}
        </h1>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="p-4 space-y-4">
          {error && (
            <div className="bg-red-900/40 border border-red-700 text-red-300 text-sm rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          {/* Tipo ingreso */}
          <div>
            <label className={labelCls}>Tipo de ingreso *</label>
            <select className={inputCls} value={form.tipo_ingreso} onChange={e => setForm(p => ({ ...p, tipo_ingreso: e.target.value as FormState['tipo_ingreso'] }))}>
              <option value="salario">Salario</option>
              <option value="aguinaldo">Aguinaldo</option>
              <option value="vacaciones">Vacaciones</option>
              <option value="liquidacion_final">Liquidación final</option>
              <option value="honorarios">Honorarios</option>
              <option value="otros">Otros</option>
            </select>
          </div>

          {/* Empleador/Contacto */}
          <div className="relative">
            <label className={labelCls}>Empleador / Pagador *</label>
            <div className="flex gap-2">
              <input
                type="text"
                className={inputCls}
                placeholder="Buscar por RUC o nombre…"
                value={contactoQuery}
                onChange={e => { setContactoQuery(e.target.value); setContactoSeleccionado(null); setMostrarDropdown(true); }}
                onFocus={() => setMostrarDropdown(true)}
                onBlur={() => setTimeout(() => setMostrarDropdown(false), 150)}
              />
              {contactoSeleccionado && (
                <button type="button" onClick={() => { setContactoSeleccionado(null); setContactoQuery(''); }} className="text-slate-400 hover:text-red-400 px-2">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                    <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                  </svg>
                </button>
              )}
            </div>
            {mostrarDropdown && sugerencias.length > 0 && (
              <div className="absolute z-10 top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-700 rounded-lg overflow-hidden shadow-xl">
                {sugerencias.map(s => (
                  <button
                    key={s.id}
                    type="button"
                    onMouseDown={() => seleccionarContacto(s)}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-slate-700 transition-colors"
                  >
                    <span className="text-slate-100">{s.razon_social}</span>
                    <span className="text-slate-500 ml-2">{s.ruc}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Período y fecha */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelCls}>Período devengado</label>
              <input type="month" className={inputCls} value={form.periodo_devengado} onChange={e => setForm(p => ({ ...p, periodo_devengado: e.target.value }))} />
            </div>
            <div>
              <label className={labelCls}>Fecha percepción</label>
              <input type="date" className={inputCls} value={form.fecha_percepcion} onChange={e => setForm(p => ({ ...p, fecha_percepcion: e.target.value }))} />
            </div>
          </div>

          {/* Montos */}
          <div>
            <label className={labelCls}>Monto bruto (Gs)</label>
            <input type="number" min="0" className={inputCls} value={form.monto_bruto} onChange={e => setForm(p => ({ ...p, monto_bruto: e.target.value }))} />
          </div>
          <div>
            <label className={labelCls}>Aporte IPS trabajador (9% auto)</label>
            <input
              type="number"
              min="0"
              className={inputCls}
              value={form.aporte_ips_trabajador}
              onChange={e => { setIpsManual(true); setForm(p => ({ ...p, aporte_ips_trabajador: e.target.value })); }}
            />
          </div>
          <div>
            <label className={labelCls}>Otros descuentos (Gs)</label>
            <input type="number" min="0" className={inputCls} value={form.otros_descuentos} onChange={e => setForm(p => ({ ...p, otros_descuentos: e.target.value }))} />
          </div>
          <div>
            <label className={labelCls}>Monto exonerado (Gs)</label>
            <input type="number" min="0" className={inputCls} value={form.monto_exonerado} onChange={e => setForm(p => ({ ...p, monto_exonerado: e.target.value }))} />
            <p className="text-xs text-slate-500 mt-1">Aguinaldo, otros conceptos exonerados de IRP.</p>
          </div>

          {/* Computable y acumulado */}
          <div className="bg-slate-800 rounded-lg px-4 py-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-400">Monto computable IRP</span>
              <span className="text-base font-bold text-white">{formatGs(computable)} Gs</span>
            </div>
            {anio > 0 && (
              <div className="flex items-center justify-between border-t border-slate-700 pt-2">
                <span className="text-xs text-slate-400">Acumulado anual {anio}</span>
                <span className={`text-sm font-semibold ${acumulado > 80_000_000 ? 'text-amber-300' : 'text-blue-300'}`}>
                  {formatGs(acumulado)} Gs
                  {acumulado > 80_000_000 && ' ⚠ Supera umbral IRP'}
                </span>
              </div>
            )}
          </div>

          {/* Notas */}
          <div>
            <label className={labelCls}>Notas</label>
            <textarea className={inputCls} rows={2} value={form.notas} onChange={e => setForm(p => ({ ...p, notas: e.target.value }))} />
          </div>
        </div>

        <div className="px-4 pb-6">
          <button
            type="submit"
            disabled={guardando}
            className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium py-2.5 rounded-lg transition-colors"
          >
            {guardando ? 'Guardando…' : 'Guardar'}
          </button>
        </div>
      </form>
    </div>
  );
}
