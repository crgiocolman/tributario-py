import { useLiveQuery } from 'dexie-react-hooks';
import { db, type ContactoLocal } from '../services/db';
import { generateUUID } from '../utils/uuid';

async function pushSync(
  tabla: string,
  registro_id: string,
  operacion: 'create' | 'update' | 'delete',
  payload: unknown
) {
  await db.sync_queue.add({
    tabla,
    registro_id,
    operacion,
    payload,
    timestamp: new Date().toISOString(),
    intentos: 0,
  });
}

export function useContactos(busqueda = '') {
  const contactos = useLiveQuery(
    () =>
      db.contactos
        .filter(c => {
          if (c.deleted_at) return false;
          if (!busqueda) return true;
          const q = busqueda.toLowerCase();
          return c.ruc.includes(q) || c.razon_social.toLowerCase().includes(q);
        })
        .toArray()
        .then(list => list.sort((a, b) => a.razon_social.localeCompare(b.razon_social))),
    [busqueda]
  );

  async function crear(
    datos: Omit<ContactoLocal, 'id' | 'created_at' | 'updated_at' | 'sync_status' | 'deleted_at'>
  ) {
    const now = new Date().toISOString();
    const contacto: ContactoLocal = {
      ...datos,
      id: generateUUID(),
      sync_status: 'pending',
      created_at: now,
      updated_at: now,
    };
    await db.contactos.put(contacto);
    await pushSync('contactos', contacto.id, 'create', contacto);
    return contacto;
  }

  async function actualizar(id: string, datos: Partial<Omit<ContactoLocal, 'id' | 'created_at'>>) {
    const now = new Date().toISOString();
    await db.contactos.update(id, { ...datos, updated_at: now, sync_status: 'pending' });
    const updated = await db.contactos.get(id);
    if (updated) await pushSync('contactos', id, 'update', updated);
  }

  async function eliminar(id: string) {
    const now = new Date().toISOString();
    await db.contactos.update(id, { deleted_at: now, updated_at: now, sync_status: 'pending' });
    await pushSync('contactos', id, 'delete', { id });
  }

  return { contactos, crear, actualizar, eliminar };
}
