import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { db } from '../services/db';
import { useContactos } from '../hooks/useContactos';

interface FormState {
  ruc: string;
  razon_social: string;
  nombre_fantasia: string;
  tipo: 'cliente' | 'proveedor' | 'ambos';
  tipo_contribuyente: 'persona_fisica' | 'persona_juridica' | '';
  telefono: string;
  email: string;
  es_frecuente: boolean;
}

const INITIAL: FormState = {
  ruc: '',
  razon_social: '',
  nombre_fantasia: '',
  tipo: 'cliente',
  tipo_contribuyente: '',
  telefono: '',
  email: '',
  es_frecuente: false,
};

const inputCls = 'w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500';
const labelCls = 'block text-xs font-medium text-slate-400 mb-1';

export default function ContactoForm() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { crear, actualizar } = useContactos();
  const [form, setForm] = useState<FormState>(INITIAL);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState('');
  const esEdicion = Boolean(id);

  useEffect(() => {
    if (!id) return;
    db.contactos.get(id).then(c => {
      if (!c) return;
      setForm({
        ruc: c.ruc,
        razon_social: c.razon_social,
        nombre_fantasia: c.nombre_fantasia ?? '',
        tipo: c.tipo,
        tipo_contribuyente: c.tipo_contribuyente ?? '',
        telefono: c.telefono ?? '',
        email: c.email ?? '',
        es_frecuente: c.es_frecuente,
      });
    });
  }, [id]);

  function set(field: keyof FormState, value: string | boolean) {
    setForm(prev => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.ruc.trim() || !form.razon_social.trim()) {
      setError('RUC y Razón social son obligatorios.');
      return;
    }
    setError('');
    setGuardando(true);
    try {
      const datos = {
        ruc: form.ruc.trim(),
        razon_social: form.razon_social.trim(),
        nombre_fantasia: form.nombre_fantasia.trim() || undefined,
        tipo: form.tipo,
        tipo_contribuyente: form.tipo_contribuyente || undefined,
        telefono: form.telefono.trim() || undefined,
        email: form.email.trim() || undefined,
        es_frecuente: form.es_frecuente,
      };
      if (esEdicion && id) {
        await actualizar(id, datos);
      } else {
        await crear(datos);
      }
      navigate('/contactos');
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
        <button onClick={() => navigate('/contactos')} className="text-slate-400 hover:text-slate-200 transition-colors">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
            <path fillRule="evenodd" d="M17 10a.75.75 0 01-.75.75H5.612l4.158 3.96a.75.75 0 11-1.04 1.08l-5.5-5.25a.75.75 0 010-1.08l5.5-5.25a.75.75 0 111.04 1.08L5.612 9.25H16.25A.75.75 0 0117 10z" clipRule="evenodd" />
          </svg>
        </button>
        <h1 className="text-lg font-bold text-white">
          {esEdicion ? 'Editar contacto' : 'Nuevo contacto'}
        </h1>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="p-4 space-y-4">
          {error && (
            <div className="bg-red-900/40 border border-red-700 text-red-300 text-sm rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          <div>
            <label className={labelCls}>RUC *</label>
            <input type="text" className={inputCls} placeholder="12345678-9" value={form.ruc} onChange={e => set('ruc', e.target.value)} />
          </div>

          <div>
            <label className={labelCls}>Razón social *</label>
            <input type="text" className={inputCls} placeholder="Empresa S.A." value={form.razon_social} onChange={e => set('razon_social', e.target.value)} />
          </div>

          <div>
            <label className={labelCls}>Nombre fantasía</label>
            <input type="text" className={inputCls} placeholder="Opcional" value={form.nombre_fantasia} onChange={e => set('nombre_fantasia', e.target.value)} />
          </div>

          <div>
            <label className={labelCls}>Tipo</label>
            <select className={inputCls} value={form.tipo} onChange={e => set('tipo', e.target.value)}>
              <option value="cliente">Cliente</option>
              <option value="proveedor">Proveedor</option>
              <option value="ambos">Cliente/Proveedor</option>
            </select>
          </div>

          <div>
            <label className={labelCls}>Tipo contribuyente</label>
            <select className={inputCls} value={form.tipo_contribuyente} onChange={e => set('tipo_contribuyente', e.target.value)}>
              <option value="">No especificado</option>
              <option value="persona_fisica">Persona física</option>
              <option value="persona_juridica">Persona jurídica</option>
            </select>
          </div>

          <div>
            <label className={labelCls}>Teléfono</label>
            <input type="tel" className={inputCls} placeholder="0981 000000" value={form.telefono} onChange={e => set('telefono', e.target.value)} />
          </div>

          <div>
            <label className={labelCls}>Email</label>
            <input type="email" className={inputCls} placeholder="contacto@empresa.com" value={form.email} onChange={e => set('email', e.target.value)} />
          </div>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              className="w-4 h-4 rounded accent-blue-500"
              checked={form.es_frecuente}
              onChange={e => set('es_frecuente', e.target.checked)}
            />
            <span className="text-sm text-slate-300">Marcar como frecuente</span>
          </label>
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
