import { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { db, type ContactoLocal, type ArchivoAdjuntoLocal } from '../services/db';
import { useComprobantes } from '../hooks/useComprobantes';
import { useCategorias } from '../hooks/useCategorias';
import { generateUUID } from '../utils/uuid';

interface FormState {
  tipo_operacion: 'compra' | 'venta';
  tipo_comprobante: 'factura' | 'autofactura' | 'ticket' | 'nota_credito' | 'nota_debito' | 'boleta_resimple' | 'liquidacion_salario';
  forma_emision: 'electronica' | 'virtual' | 'preimpresa' | 'autoimpresor' | 'no_aplica';
  fecha_emision: string;
  numero_timbrado: string;
  numero_comprobante: string;
  condicion: 'contado' | 'credito';
  forma_pago: 'efectivo' | 'transferencia' | 'tarjeta_credito' | 'tarjeta_debito' | 'cheque' | 'mixto' | '';
  monto_exento: string;
  monto_gravado_5: string;
  monto_gravado_10: string;
  concepto: string;
  notas: string;
  cargado_marangatu: 'si' | 'no' | 'auto';
  iva_incluido: boolean;
}

interface ImputacionState {
  categoria_irp_id: string;
  imputa_iva_credito: boolean;
  iva_credito_porcentaje: number;
  imputa_irp: boolean;
  destino_reg_comprobante: 'IVA' | 'IRP-RSP' | 'NO_IMPUTAR';
}

const INITIAL_FORM: FormState = {
  tipo_operacion: 'compra',
  tipo_comprobante: 'factura',
  forma_emision: 'electronica',
  fecha_emision: new Date().toISOString().slice(0, 10),
  numero_timbrado: '',
  numero_comprobante: '',
  condicion: 'contado',
  forma_pago: 'efectivo',
  monto_exento: '0',
  monto_gravado_5: '0',
  monto_gravado_10: '0',
  concepto: '',
  notas: '',
  cargado_marangatu: 'auto',
  iva_incluido: true,
};

const INITIAL_IMP: ImputacionState = {
  categoria_irp_id: '',
  imputa_iva_credito: false,
  iva_credito_porcentaje: 0,
  imputa_irp: false,
  destino_reg_comprobante: 'NO_IMPUTAR',
};

const inputCls = 'w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500';
const labelCls = 'block text-xs font-medium text-slate-400 mb-1';
const readonlyCls = 'w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-sm text-slate-300';
const sectionCls = 'pt-4 pb-2 text-xs font-semibold text-slate-400 uppercase tracking-wider';

const formatGs = (n: number) => new Intl.NumberFormat('es-PY').format(n);
const toInt = (s: string) => Math.max(0, Math.round(Number(s.replace(/\D/g, '')) || 0));

export default function ComprobanteForm() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { crear, actualizar } = useComprobantes();
  const { categorias, loading: loadingCats } = useCategorias();
  const esEdicion = Boolean(id);

  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [imp, setImp] = useState<ImputacionState>(INITIAL_IMP);
  const [contactoQuery, setContactoQuery] = useState('');
  const [contactoSeleccionado, setContactoSeleccionado] = useState<ContactoLocal | null>(null);
  const [sugerencias, setSugerencias] = useState<ContactoLocal[]>([]);
  const [mostrarDropdown, setMostrarDropdown] = useState(false);
  const [adjuntoFile, setAdjuntoFile] = useState<File | null>(null);
  const [adjuntoPreviewUrl, setAdjuntoPreviewUrl] = useState<string | null>(null);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState('');
  const montosRef = useRef<HTMLDivElement>(null);
  const location = useLocation();

  // Derivados
  const exento = toInt(form.monto_exento);
  const gravado5 = toInt(form.monto_gravado_5);
  const gravado10 = toInt(form.monto_gravado_10);
  const iva5 = form.iva_incluido
    ? Math.round(gravado5 * 5 / 105)
    : Math.round(gravado5 * 0.05);
  const iva10 = form.iva_incluido
    ? Math.round(gravado10 * 10 / 110)
    : Math.round(gravado10 * 0.10);
  const total = form.iva_incluido
    ? exento + gravado5 + gravado10
    : exento + gravado5 + iva5 + gravado10 + iva10;
  const periodo_fiscal = form.fecha_emision ? form.fecha_emision.slice(0, 7) : '';

  // Preview URL para adjunto de imagen
  useEffect(() => {
    if (!adjuntoFile?.type.startsWith('image/')) {
      setAdjuntoPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(adjuntoFile);
    setAdjuntoPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [adjuntoFile]);

  // Archivo pre-cargado desde captura de cámara (navigation state)
  useEffect(() => {
    if (id) return;
    const state = location.state as { pendingFile?: File } | null;
    if (state?.pendingFile) {
      setAdjuntoFile(state.pendingFile);
      setTimeout(() => montosRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 300);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Cargar datos en modo edición
  useEffect(() => {
    if (!id) return;
    db.comprobantes.get(id).then(async c => {
      if (!c) return;
      setForm({
        tipo_operacion: c.tipo_operacion,
        tipo_comprobante: c.tipo_comprobante,
        forma_emision: c.forma_emision,
        fecha_emision: c.fecha_emision,
        numero_timbrado: c.numero_timbrado ?? '',
        numero_comprobante: c.numero_comprobante ?? '',
        condicion: c.condicion,
        forma_pago: c.forma_pago ?? '',
        monto_exento: String(c.monto_exento),
        monto_gravado_5: String(c.monto_gravado_5),
        monto_gravado_10: String(c.monto_gravado_10),
        concepto: c.concepto ?? '',
        notas: c.notas ?? '',
        cargado_marangatu: c.cargado_marangatu,
        iva_incluido: true,
      });
      const contacto = await db.contactos.get(c.contacto_id);
      if (contacto) {
        setContactoSeleccionado(contacto);
        setContactoQuery(contacto.razon_social);
      }
      const imputacion = await db.imputaciones.where('comprobante_id').equals(id).first();
      if (imputacion) {
        setImp({
          categoria_irp_id: imputacion.categoria_irp_id,
          imputa_iva_credito: imputacion.imputa_iva_credito,
          iva_credito_porcentaje: imputacion.iva_credito_porcentaje,
          imputa_irp: imputacion.imputa_irp,
          destino_reg_comprobante: imputacion.destino_reg_comprobante,
        });
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

  function limpiarContacto() {
    setContactoSeleccionado(null);
    setContactoQuery('');
  }

  function handleCategoriaChange(categoriaId: string) {
    const cat = categorias.find(c => c.id === categoriaId);
    setImp(prev => ({
      ...prev,
      categoria_irp_id: categoriaId,
      imputa_iva_credito: cat?.imputa_iva_credito ?? false,
      iva_credito_porcentaje: cat?.iva_credito_porcentaje ?? 0,
      imputa_irp: cat?.imputa_irp ?? false,
      destino_reg_comprobante: (cat?.destino_reg_comprobante as ImputacionState['destino_reg_comprobante']) ?? 'NO_IMPUTAR',
    }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!contactoSeleccionado) {
      setError('Seleccioná un contacto.');
      return;
    }
    if (!form.fecha_emision) {
      setError('La fecha de emisión es obligatoria.');
      return;
    }
    if (total === 0) {
      setError('El total no puede ser cero.');
      return;
    }
    setError('');
    setGuardando(true);

    try {
      const ivaCreditoMonto = imp.imputa_iva_credito
        ? Math.round((iva5 + iva10) * imp.iva_credito_porcentaje / 100)
        : 0;

      const datosComprobante = {
        contacto_id: contactoSeleccionado.id,
        tipo_operacion: form.tipo_operacion,
        tipo_comprobante: form.tipo_comprobante,
        forma_emision: form.forma_emision,
        fecha_emision: form.fecha_emision,
        numero_timbrado: form.numero_timbrado.trim() || undefined,
        numero_comprobante: form.numero_comprobante.trim() || undefined,
        condicion: form.condicion,
        moneda: 'PYG',
        forma_pago: form.forma_pago || undefined,
        monto_exento: exento,
        monto_gravado_5: gravado5,
        iva_5: iva5,
        monto_gravado_10: gravado10,
        iva_10: iva10,
        total,
        periodo_fiscal,
        concepto: form.concepto.trim() || undefined,
        notas: form.notas.trim() || undefined,
        cargado_marangatu: form.cargado_marangatu,
      };

      const imputacionDatos = {
        categoria_irp_id: imp.categoria_irp_id,
        imputa_iva_credito: imp.imputa_iva_credito,
        iva_credito_porcentaje: imp.iva_credito_porcentaje,
        iva_credito_monto: ivaCreditoMonto,
        imputa_irp: imp.imputa_irp,
        destino_reg_comprobante: imp.destino_reg_comprobante,
        rectificado: false,
      };

      let comprobanteId: string;
      if (esEdicion && id) {
        await actualizar(id, datosComprobante, imputacionDatos);
        comprobanteId = id;
      } else {
        const comp = await crear(datosComprobante, imputacionDatos);
        comprobanteId = comp.id;
      }

      if (adjuntoFile) {
        const adjunto: ArchivoAdjuntoLocal = {
          id: generateUUID(),
          comprobante_id: comprobanteId,
          nombre_archivo: adjuntoFile.name,
          tipo_mime: adjuntoFile.type,
          tamano_bytes: adjuntoFile.size,
          blob: adjuntoFile,
          sync_status: 'pending',
          created_at: new Date().toISOString(),
        };
        await db.adjuntos.put(adjunto);
        await db.sync_queue.add({
          tabla: 'adjuntos',
          registro_id: adjunto.id,
          operacion: 'create',
          payload: { id: adjunto.id, comprobante_id: adjunto.comprobante_id },
          timestamp: adjunto.created_at,
          intentos: 0,
        });
      }

      navigate('/comprobantes');
    } catch (err) {
      setError('Error al guardar. Intentá de nuevo.');
      console.error(err);
    } finally {
      setGuardando(false);
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 pt-5 pb-4 border-b border-slate-800">
        <button onClick={() => navigate('/comprobantes')} className="text-slate-400 hover:text-slate-200 transition-colors">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
            <path fillRule="evenodd" d="M17 10a.75.75 0 01-.75.75H5.612l4.158 3.96a.75.75 0 11-1.04 1.08l-5.5-5.25a.75.75 0 010-1.08l5.5-5.25a.75.75 0 111.04 1.08L5.612 9.25H16.25A.75.75 0 0117 10z" clipRule="evenodd" />
          </svg>
        </button>
        <h1 className="text-lg font-bold text-white">
          {esEdicion ? 'Editar comprobante' : 'Nuevo comprobante'}
        </h1>
      </div>

      <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto">
        <div className="p-4 space-y-4">
          {error && (
            <div className="bg-red-900/40 border border-red-700 text-red-300 text-sm rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          {/* Tipo operación */}
          <div>
            <p className={labelCls}>Tipo de operación *</p>
            <div className="flex gap-2">
              {(['compra', 'venta'] as const).map(t => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setForm(p => ({ ...p, tipo_operacion: t }))}
                  className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${form.tipo_operacion === t ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}
                >
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Tipo comprobante */}
          <div>
            <label className={labelCls}>Tipo de comprobante</label>
            <select className={inputCls} value={form.tipo_comprobante} onChange={e => setForm(p => ({ ...p, tipo_comprobante: e.target.value as FormState['tipo_comprobante'] }))}>
              <option value="factura">Factura</option>
              <option value="autofactura">Autofactura</option>
              <option value="ticket">Ticket</option>
              <option value="nota_credito">Nota de crédito</option>
              <option value="nota_debito">Nota de débito</option>
              <option value="boleta_resimple">Boleta ReSiMPle</option>
              <option value="liquidacion_salario">Liquidación de salario</option>
            </select>
          </div>

          {/* Forma emisión */}
          <div>
            <label className={labelCls}>Forma de emisión</label>
            <select className={inputCls} value={form.forma_emision} onChange={e => setForm(p => ({ ...p, forma_emision: e.target.value as FormState['forma_emision'] }))}>
              <option value="electronica">Electrónica</option>
              <option value="virtual">Virtual</option>
              <option value="preimpresa">Preimpresa</option>
              <option value="autoimpresor">Autoimpresor</option>
              <option value="no_aplica">No aplica</option>
            </select>
          </div>

          {/* Fecha */}
          <div>
            <label className={labelCls}>Fecha de emisión *</label>
            <input type="date" className={inputCls} value={form.fecha_emision} onChange={e => setForm(p => ({ ...p, fecha_emision: e.target.value }))} />
          </div>

          {/* Contacto */}
          <div className="relative">
            <label className={labelCls}>Contacto *</label>
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
                <button type="button" onClick={limpiarContacto} className="text-slate-400 hover:text-red-400 px-2">
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

          {/* Numeración */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelCls}>Timbrado</label>
              <input type="text" className={inputCls} placeholder="12345678" value={form.numero_timbrado} onChange={e => setForm(p => ({ ...p, numero_timbrado: e.target.value }))} />
            </div>
            <div>
              <label className={labelCls}>Nro. comprobante</label>
              <input type="text" className={inputCls} placeholder="001-001-0000001" value={form.numero_comprobante} onChange={e => setForm(p => ({ ...p, numero_comprobante: e.target.value }))} />
            </div>
          </div>

          {/* Condición y pago */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelCls}>Condición</label>
              <select className={inputCls} value={form.condicion} onChange={e => setForm(p => ({ ...p, condicion: e.target.value as FormState['condicion'] }))}>
                <option value="contado">Contado</option>
                <option value="credito">Crédito</option>
              </select>
            </div>
            <div>
              <label className={labelCls}>Forma de pago</label>
              <select className={inputCls} value={form.forma_pago} onChange={e => setForm(p => ({ ...p, forma_pago: e.target.value as FormState['forma_pago'] }))}>
                <option value="">No especificado</option>
                <option value="efectivo">Efectivo</option>
                <option value="transferencia">Transferencia</option>
                <option value="tarjeta_credito">Tarjeta crédito</option>
                <option value="tarjeta_debito">Tarjeta débito</option>
                <option value="cheque">Cheque</option>
                <option value="mixto">Mixto</option>
              </select>
            </div>
          </div>

          {/* Montos */}
          <div ref={montosRef} className="flex items-center justify-between pt-4 pb-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Montos (en Guaraníes)</span>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                className="accent-blue-500"
                checked={form.iva_incluido}
                onChange={e => setForm(p => ({ ...p, iva_incluido: e.target.checked }))}
              />
              <span className="text-xs text-slate-400">IVA incluido</span>
            </label>
          </div>
          <div>
            <label className={labelCls}>Exento</label>
            <input type="number" min="0" className={inputCls} value={form.monto_exento} onChange={e => setForm(p => ({ ...p, monto_exento: e.target.value }))} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelCls}>Gravado 5% {form.iva_incluido ? '(IVA inc.)' : '(base neta)'}</label>
              <input type="number" min="0" className={inputCls} value={form.monto_gravado_5} onChange={e => setForm(p => ({ ...p, monto_gravado_5: e.target.value }))} />
            </div>
            <div>
              <label className={labelCls}>IVA 5% (auto)</label>
              <div className={readonlyCls}>{formatGs(iva5)}</div>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelCls}>Gravado 10% {form.iva_incluido ? '(IVA inc.)' : '(base neta)'}</label>
              <input type="number" min="0" className={inputCls} value={form.monto_gravado_10} onChange={e => setForm(p => ({ ...p, monto_gravado_10: e.target.value }))} />
            </div>
            <div>
              <label className={labelCls}>IVA 10% (auto)</label>
              <div className={readonlyCls}>{formatGs(iva10)}</div>
            </div>
          </div>
          <div className="bg-slate-800 rounded-lg px-4 py-3 flex items-center justify-between">
            <span className="text-sm text-slate-400">Total</span>
            <span className="text-lg font-bold text-white">{formatGs(total)} Gs</span>
          </div>

          {/* Concepto y notas */}
          <div>
            <label className={labelCls}>Concepto</label>
            <input type="text" className={inputCls} placeholder="Descripción del comprobante" value={form.concepto} onChange={e => setForm(p => ({ ...p, concepto: e.target.value }))} />
          </div>
          <div>
            <label className={labelCls}>Notas internas</label>
            <textarea className={inputCls} rows={2} value={form.notas} onChange={e => setForm(p => ({ ...p, notas: e.target.value }))} />
          </div>

          {/* Marangatú */}
          <div>
            <label className={labelCls}>Cargado en Marangatú</label>
            <select className={inputCls} value={form.cargado_marangatu} onChange={e => setForm(p => ({ ...p, cargado_marangatu: e.target.value as FormState['cargado_marangatu'] }))}>
              <option value="auto">Automático</option>
              <option value="si">Sí</option>
              <option value="no">No</option>
            </select>
          </div>

          {/* Categoría IRP e imputación */}
          <p className={sectionCls}>Imputación fiscal (IRP)</p>
          <div>
            <label className={labelCls}>Categoría IRP</label>
            <select
              className={inputCls}
              value={imp.categoria_irp_id}
              onChange={e => handleCategoriaChange(e.target.value)}
              disabled={loadingCats}
            >
              <option value="">Sin imputar</option>
              {categorias.map(c => (
                <option key={c.id} value={c.id}>{c.nombre}</option>
              ))}
            </select>
          </div>
          {imp.categoria_irp_id && (
            <>
              <div className="grid grid-cols-2 gap-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" className="accent-blue-500" checked={imp.imputa_iva_credito} onChange={e => setImp(p => ({ ...p, imputa_iva_credito: e.target.checked }))} />
                  <span className="text-sm text-slate-300">Imputa IVA crédito</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" className="accent-blue-500" checked={imp.imputa_irp} onChange={e => setImp(p => ({ ...p, imputa_irp: e.target.checked }))} />
                  <span className="text-sm text-slate-300">Imputa IRP</span>
                </label>
              </div>
              {imp.imputa_iva_credito && (
                <div>
                  <label className={labelCls}>% IVA crédito</label>
                  <input type="number" min="0" max="100" className={inputCls} value={imp.iva_credito_porcentaje} onChange={e => setImp(p => ({ ...p, iva_credito_porcentaje: Number(e.target.value) }))} />
                </div>
              )}
              <div>
                <label className={labelCls}>Destino registro comprobante</label>
                <select className={inputCls} value={imp.destino_reg_comprobante} onChange={e => setImp(p => ({ ...p, destino_reg_comprobante: e.target.value as ImputacionState['destino_reg_comprobante'] }))}>
                  <option value="NO_IMPUTAR">No imputar</option>
                  <option value="IVA">IVA</option>
                  <option value="IRP-RSP">IRP-RSP</option>
                </select>
              </div>
            </>
          )}

          {/* Adjunto */}
          <p className={sectionCls}>Adjunto</p>
          {adjuntoPreviewUrl && (
            <div className="relative rounded-lg overflow-hidden">
              <img src={adjuntoPreviewUrl} alt="Vista previa" className="w-full max-h-52 object-cover rounded-lg" />
              <button
                type="button"
                onClick={() => setAdjuntoFile(null)}
                className="absolute top-2 right-2 bg-slate-900/70 hover:bg-red-900/70 text-white rounded-full p-1.5 transition-colors"
                aria-label="Quitar foto"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
                  <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                </svg>
              </button>
            </div>
          )}
          <div>
            <label className={labelCls}>Foto o PDF del comprobante</label>
            <div className="flex gap-2">
              <label className="flex-1 cursor-pointer">
                <input
                  type="file"
                  accept="image/*,application/pdf"
                  className="hidden"
                  onChange={e => setAdjuntoFile(e.target.files?.[0] ?? null)}
                />
                <div className="w-full text-center text-sm text-slate-400 border border-dashed border-slate-600 rounded-lg py-2 px-3 hover:border-slate-500 transition-colors">
                  {adjuntoFile ? adjuntoFile.name : 'Elegir archivo'}
                </div>
              </label>
              <label className="cursor-pointer shrink-0" title="Tomar foto con cámara">
                <input
                  type="file"
                  accept="image/*"
                  capture="environment"
                  className="hidden"
                  onChange={e => setAdjuntoFile(e.target.files?.[0] ?? null)}
                />
                <div className="bg-slate-700 hover:bg-slate-600 rounded-lg px-3 py-2 flex items-center justify-center transition-colors">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-slate-300">
                    <path d="M12 9a3.75 3.75 0 100 7.5A3.75 3.75 0 0012 9z" />
                    <path fillRule="evenodd" d="M9.344 3.071a49.52 49.52 0 015.312 0c.967.052 1.83.585 2.332 1.39l.821 1.317c.24.383.645.643 1.11.71.386.054.77.113 1.152.177 1.432.239 2.429 1.493 2.429 2.909V18a3 3 0 01-3 3h-15a3 3 0 01-3-3V9.574c0-1.416.997-2.67 2.429-2.909.382-.064.766-.123 1.151-.178a1.56 1.56 0 001.11-.71l.822-1.315a2.942 2.942 0 012.332-1.39zM6.75 12.75a5.25 5.25 0 1110.5 0 5.25 5.25 0 01-10.5 0zM12 10.5a2.25 2.25 0 100 4.5 2.25 2.25 0 000-4.5z" clipRule="evenodd" />
                  </svg>
                </div>
              </label>
            </div>
            {adjuntoFile && !adjuntoPreviewUrl && (
              <p className="text-xs text-slate-500 mt-1">{adjuntoFile.name} ({(adjuntoFile.size / 1024).toFixed(0)} KB)</p>
            )}
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
