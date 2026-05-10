import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../services/db';

const MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

// Escala progresiva IRP-RSP. 80M es umbral de entrada (no mínimo no imponible).
function calcularIRP(rentaNeta: number): number {
  if (rentaNeta < 80_000_000) return 0;
  let imp = Math.min(rentaNeta, 50_000_000) * 0.08;
  if (rentaNeta > 50_000_000) {
    imp += Math.min(rentaNeta - 50_000_000, 100_000_000) * 0.09;
  }
  if (rentaNeta > 150_000_000) {
    imp += (rentaNeta - 150_000_000) * 0.1;
  }
  return Math.round(imp);
}

export interface IvaAnualItem {
  mes: string;
  debito: number;
  credito: number;
}

export interface EgresoCategoriaItem {
  nombre: string;
  valor: number;
}

export interface VencimientoItem {
  tipo: string;
  fecha: string;
  diasRestantes: number;
}

export interface DashboardData {
  periodoActual: string;
  cantidadComprobantes: number;
  ivaDebito: number;
  ivaCredito: number;
  saldoIva: number;
  anioActual: number;
  ivaAnual: IvaAnualItem[];
  egresosPorCategoria: EgresoCategoriaItem[];
  ingresosComputables: number;
  egresosDeducibles: number;
  rentaNeta: number;
  impuestoEstimado: number;
  proximosVencimientos: VencimientoItem[];
}

export function useDashboard(): DashboardData | undefined {
  const hoy = new Date();
  const anio = hoy.getFullYear();
  const mesIdx = hoy.getMonth();
  const periodoActual = `${anio}-${String(mesIdx + 1).padStart(2, '0')}`;

  return useLiveQuery(async () => {
    const [todosComprobantes, todasImputaciones, todasCategorias, todosIngresos] = await Promise.all([
      db.comprobantes.filter(c => !c.deleted_at).toArray(),
      db.imputaciones.toArray(),
      db.categorias_irp.toArray(),
      db.ingresos.filter(i => !i.deleted_at).toArray(),
    ]);

    const impMap = new Map(todasImputaciones.map(i => [i.comprobante_id, i]));
    const catMap = new Map(todasCategorias.map(c => [c.id, c.nombre]));

    // Resumen mes actual
    const comprobantesDelMes = todosComprobantes.filter(c => c.periodo_fiscal === periodoActual);
    const ivaDebito = comprobantesDelMes
      .filter(c => c.tipo_operacion === 'venta')
      .reduce((acc, c) => acc + c.iva_5 + c.iva_10, 0);
    const ivaCredito = comprobantesDelMes
      .filter(c => c.tipo_operacion === 'compra')
      .reduce((acc, c) => {
        const imp = impMap.get(c.id);
        return acc + (imp?.imputa_iva_credito ? imp.iva_credito_monto : 0);
      }, 0);

    // IVA anual (12 meses)
    const comprobantesAnio = todosComprobantes.filter(c => c.periodo_fiscal.startsWith(String(anio)));
    const ivaAnual: IvaAnualItem[] = MESES.map((mes, i) => {
      const mesStr = `${anio}-${String(i + 1).padStart(2, '0')}`;
      const mc = comprobantesAnio.filter(c => c.periodo_fiscal === mesStr);
      const debito = mc
        .filter(c => c.tipo_operacion === 'venta')
        .reduce((acc, c) => acc + c.iva_5 + c.iva_10, 0);
      const credito = mc
        .filter(c => c.tipo_operacion === 'compra')
        .reduce((acc, c) => {
          const imp = impMap.get(c.id);
          return acc + (imp?.imputa_iva_credito ? imp.iva_credito_monto : 0);
        }, 0);
      return { mes, debito, credito };
    });

    // Egresos por categoría IRP (año)
    const egresosCatMap = new Map<string, number>();
    comprobantesAnio
      .filter(c => c.tipo_operacion === 'compra')
      .forEach(c => {
        const imp = impMap.get(c.id);
        if (imp?.imputa_irp) {
          const nombre = catMap.get(imp.categoria_irp_id) ?? 'Sin categoría';
          egresosCatMap.set(nombre, (egresosCatMap.get(nombre) ?? 0) + c.total);
        }
      });
    const egresosPorCategoria: EgresoCategoriaItem[] = Array.from(egresosCatMap.entries())
      .map(([nombre, valor]) => ({ nombre, valor }))
      .sort((a, b) => b.valor - a.valor)
      .slice(0, 8);

    // Proyección IRP
    const ingresosComputables = todosIngresos
      .filter(i => i.periodo_devengado.startsWith(String(anio)) && i.es_gravado_irp)
      .reduce((acc, i) => acc + i.monto_computable_irp, 0);
    const egresosDeducibles = Array.from(egresosCatMap.values()).reduce((a, b) => a + b, 0);
    const rentaNeta = Math.max(0, ingresosComputables - egresosDeducibles);
    const impuestoEstimado = calcularIRP(rentaNeta);

    // Próximos vencimientos: F120 día 25, Reg. Comprob. día 26.
    // Se muestran dos períodos: el anterior (vence este mes) y el actual (vence el mes que viene).
    const diffDays = (d: Date) => Math.ceil((d.getTime() - hoy.getTime()) / (1000 * 60 * 60 * 24));
    const candidatos = [
      // Período anterior → vence este mes
      { tipo: 'F120 (IVA)', fecha: new Date(anio, mesIdx, 25) },
      { tipo: 'Reg. Comprob.', fecha: new Date(anio, mesIdx, 26) },
      // Período actual → vence el mes que viene
      { tipo: 'F120 (IVA)', fecha: new Date(anio, mesIdx + 1, 25) },
      { tipo: 'Reg. Comprob.', fecha: new Date(anio, mesIdx + 1, 26) },
    ];
    // Deduplicar: si el mismo tipo aparece dos veces, quedarse con el más próximo que no haya vencido
    const seen = new Set<string>();
    const proximosVencimientos: VencimientoItem[] = candidatos
      .map(v => ({ tipo: v.tipo, fecha: v.fecha.toISOString().slice(0, 10), diasRestantes: diffDays(v.fecha) }))
      .filter(v => v.diasRestantes >= 0)
      .filter(v => {
        if (seen.has(v.tipo)) return false;
        seen.add(v.tipo);
        return true;
      })
      .filter(v => v.diasRestantes <= 45);

    return {
      periodoActual,
      cantidadComprobantes: comprobantesDelMes.length,
      ivaDebito,
      ivaCredito,
      saldoIva: ivaDebito - ivaCredito,
      anioActual: anio,
      ivaAnual,
      egresosPorCategoria,
      ingresosComputables,
      egresosDeducibles,
      rentaNeta,
      impuestoEstimado,
      proximosVencimientos,
    };
  }, []);
}
