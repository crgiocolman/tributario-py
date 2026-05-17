import { useLiveQuery } from 'dexie-react-hooks';
import { db, type IngresoLocal } from '../services/db';
import { generateUUID } from '../utils/uuid';
import { push } from '../services/sync';

async function pushSync(
  tabla: string,
  registro_id: string,
  operacion: 'create' | 'update' | 'delete',
  payload: unknown
) {
  if (operacion === 'update') {
    const allExisting = await db.sync_queue.where('registro_id').equals(registro_id).toArray();
    const createItem = allExisting.find(i => i.operacion === 'create');
    const updateItem = allExisting.find(i => i.operacion === 'update');

    if (createItem?.autoId != null) {
      await db.sync_queue.update(createItem.autoId, {
        payload, timestamp: new Date().toISOString(), intentos: 0, ultimo_error: undefined,
      });
      if (updateItem?.autoId != null) await db.sync_queue.delete(updateItem.autoId);
      push();
      return;
    }

    if (updateItem?.autoId != null) {
      await db.sync_queue.update(updateItem.autoId, {
        payload, timestamp: new Date().toISOString(), intentos: 0, ultimo_error: undefined,
      });
      push();
      return;
    }
  }

  await db.sync_queue.add({
    tabla, registro_id, operacion, payload, timestamp: new Date().toISOString(), intentos: 0,
  });
  push();
}

interface FiltrosIngresos {
  anio?: number;
  tipo_ingreso?: string;
}

export function useIngresos(filtros: FiltrosIngresos = {}) {
  const ingresos = useLiveQuery(
    () =>
      db.ingresos
        .filter(i => {
          if (i.deleted_at) return false;
          if (filtros.anio && !i.periodo_devengado.startsWith(String(filtros.anio))) return false;
          if (filtros.tipo_ingreso && i.tipo_ingreso !== filtros.tipo_ingreso) return false;
          return true;
        })
        .toArray()
        .then(list => list.sort((a, b) => b.periodo_devengado.localeCompare(a.periodo_devengado))),
    [filtros.anio, filtros.tipo_ingreso]
  );

  async function calcularAcumuladoAnual(anio: number, excluirId?: string): Promise<number> {
    const todos = await db.ingresos
      .filter(
        i =>
          !i.deleted_at &&
          i.periodo_devengado.startsWith(String(anio)) &&
          i.id !== excluirId
      )
      .toArray();
    return todos.reduce((acc, i) => acc + i.monto_computable_irp, 0);
  }

  async function crear(
    datos: Omit<IngresoLocal, 'id' | 'created_at' | 'updated_at' | 'sync_status' | 'deleted_at'>
  ) {
    const now = new Date().toISOString();
    const ingreso: IngresoLocal = {
      ...datos,
      id: generateUUID(),
      sync_status: 'pending',
      created_at: now,
      updated_at: now,
    };
    await db.ingresos.put(ingreso);
    await pushSync('ingresos', ingreso.id, 'create', ingreso);
    return ingreso;
  }

  async function actualizar(id: string, datos: Partial<Omit<IngresoLocal, 'id' | 'created_at'>>) {
    const now = new Date().toISOString();
    await db.ingresos.update(id, { ...datos, updated_at: now, sync_status: 'pending' });
    const updated = await db.ingresos.get(id);
    if (updated) await pushSync('ingresos', id, 'update', updated);
  }

  async function eliminar(id: string) {
    const now = new Date().toISOString();
    await db.ingresos.update(id, { deleted_at: now, updated_at: now, sync_status: 'pending' });
    await pushSync('ingresos', id, 'delete', { id });
  }

  return { ingresos, calcularAcumuladoAnual, crear, actualizar, eliminar };
}
