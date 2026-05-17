import { useLiveQuery } from 'dexie-react-hooks';
import { db, type ComprobanteLocal, type ImputacionFiscalLocal } from '../services/db';
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

interface FiltrosComprobantes {
  periodo_fiscal?: string;
  tipo_operacion?: string;
}

export type ImputacionInput = Omit<ImputacionFiscalLocal, 'id' | 'comprobante_id' | 'created_at' | 'updated_at'>;

export function useComprobantes(filtros: FiltrosComprobantes = {}) {
  const comprobantes = useLiveQuery(
    () =>
      db.comprobantes
        .orderBy('fecha_emision')
        .reverse()
        .filter(c => {
          if (c.deleted_at) return false;
          if (filtros.periodo_fiscal && c.periodo_fiscal !== filtros.periodo_fiscal) return false;
          if (filtros.tipo_operacion && c.tipo_operacion !== filtros.tipo_operacion) return false;
          return true;
        })
        .toArray(),
    [filtros.periodo_fiscal, filtros.tipo_operacion]
  );

  async function crear(
    datos: Omit<ComprobanteLocal, 'id' | 'created_at' | 'updated_at' | 'sync_status' | 'deleted_at'>,
    imputacion: ImputacionInput
  ) {
    const now = new Date().toISOString();
    const comprobanteId = generateUUID();
    const comprobante: ComprobanteLocal = {
      ...datos,
      id: comprobanteId,
      sync_status: 'pending',
      created_at: now,
      updated_at: now,
    };
    const imputacionRecord: ImputacionFiscalLocal = {
      ...imputacion,
      id: generateUUID(),
      comprobante_id: comprobanteId,
      created_at: now,
      updated_at: now,
    };
    await db.transaction('rw', [db.comprobantes, db.imputaciones], async () => {
      await db.comprobantes.put(comprobante);
      await db.imputaciones.put(imputacionRecord);
    });
    await pushSync('comprobantes', comprobanteId, 'create', comprobante);
    await pushSync('imputaciones_fiscales', imputacionRecord.id, 'create', imputacionRecord);
    return comprobante;
  }

  async function actualizar(
    id: string,
    datos: Partial<Omit<ComprobanteLocal, 'id' | 'created_at'>>,
    imputacion?: Partial<ImputacionFiscalLocal>
  ) {
    const now = new Date().toISOString();
    await db.transaction('rw', [db.comprobantes, db.imputaciones], async () => {
      await db.comprobantes.update(id, { ...datos, updated_at: now, sync_status: 'pending' });
      if (imputacion) {
        const existing = await db.imputaciones.where('comprobante_id').equals(id).first();
        if (existing) {
          await db.imputaciones.update(existing.id, { ...imputacion, updated_at: now });
        }
      }
    });
    const updated = await db.comprobantes.get(id);
    if (updated) await pushSync('comprobantes', id, 'update', updated);
    if (imputacion) {
      const updatedImp = await db.imputaciones.where('comprobante_id').equals(id).first();
      if (updatedImp) await pushSync('imputaciones_fiscales', updatedImp.id, 'update', updatedImp);
    }
  }

  async function eliminar(id: string) {
    const now = new Date().toISOString();
    await db.comprobantes.update(id, { deleted_at: now, updated_at: now, sync_status: 'pending' });
    await pushSync('comprobantes', id, 'delete', { id });
  }

  return { comprobantes, crear, actualizar, eliminar };
}
