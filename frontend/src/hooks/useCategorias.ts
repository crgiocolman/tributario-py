import { useEffect, useState } from 'react';
import { db, type CategoriaIRPLocal } from '../services/db';
import { api } from '../services/api';

export interface ApiCategoria {
  id: string;
  codigo: string;
  nombre: string;
  descripcion?: string;
  articulo_ley?: string;
  limite_porcentaje?: number | null;
  activo: boolean;
  orden: number;
  regla_imputacion?: {
    imputa_iva_credito: boolean;
    imputa_iva_credito_porcentaje?: number | null;
    imputa_irp: boolean;
    destino_reg_comprobante: string;
  } | null;
}

export const DESTINO_MAP: Record<string, string> = {
  irp_rsp: 'IRP-RSP',
  iva: 'IVA',
  no_imputar: 'NO_IMPUTAR',
};

export function mapCategoria(c: ApiCategoria): CategoriaIRPLocal {
  return {
    id: c.id,
    codigo: c.codigo,
    nombre: c.nombre,
    descripcion: c.descripcion,
    articulo_ley: c.articulo_ley,
    limite_porcentaje: c.limite_porcentaje ?? undefined,
    activo: c.activo,
    orden: c.orden,
    imputa_iva_credito: c.regla_imputacion?.imputa_iva_credito ?? false,
    iva_credito_porcentaje: c.regla_imputacion?.imputa_iva_credito_porcentaje ?? undefined,
    imputa_irp: c.regla_imputacion?.imputa_irp ?? false,
    destino_reg_comprobante: DESTINO_MAP[c.regla_imputacion?.destino_reg_comprobante ?? ''] ?? 'NO_IMPUTAR',
  };
}

export function useCategorias() {
  const [categorias, setCategorias] = useState<CategoriaIRPLocal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      let all = await db.categorias_irp.toArray();
      let valid = all.filter(c => c.activo);

      // Fetch if IDB is empty or contains only malformed records (from a prior bug)
      if (valid.length === 0) {
        try {
          const response = await api.get<{ data: ApiCategoria[] }>('/categorias-irp');
          const mapped = (response.data ?? []).map(mapCategoria);
          if (mapped.length > 0) {
            await db.categorias_irp.clear();
            await db.categorias_irp.bulkPut(mapped);
            all = mapped;
            valid = mapped.filter(c => c.activo);
          }
        } catch {
          // Sin conexión — continúa con IDB
        }
      }

      if (!cancelled) {
        setCategorias(valid.sort((a, b) => a.orden - b.orden));
        setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, []);

  return { categorias, loading };
}
