import Dexie, { type Table } from 'dexie';

export interface ContactoLocal {
  id: string;
  ruc: string;
  razon_social: string;
  nombre_fantasia?: string;
  tipo: 'cliente' | 'proveedor' | 'ambos';
  tipo_contribuyente?: 'persona_fisica' | 'persona_juridica';
  telefono?: string;
  email?: string;
  direccion?: string;
  notas?: string;
  es_frecuente: boolean;
  sync_status: 'pending' | 'synced' | 'conflict';
  device_id?: string;
  created_at: string;
  updated_at: string;
  deleted_at?: string;
}

export interface ComprobanteLocal {
  id: string;
  contacto_id: string;
  tipo_operacion: 'compra' | 'venta';
  tipo_comprobante: 'factura' | 'autofactura' | 'ticket' | 'nota_credito' | 'nota_debito' | 'boleta_resimple' | 'liquidacion_salario';
  forma_emision: 'electronica' | 'virtual' | 'preimpresa' | 'autoimpresor' | 'no_aplica';
  numero_timbrado?: string;
  numero_comprobante?: string;
  fecha_emision: string;
  fecha_percepcion?: string;
  condicion: 'contado' | 'credito';
  moneda: string;
  tipo_cambio?: number;
  monto_exento: number;
  monto_gravado_5: number;
  iva_5: number;
  monto_gravado_10: number;
  iva_10: number;
  total: number;
  forma_pago?: 'efectivo' | 'transferencia' | 'tarjeta_credito' | 'tarjeta_debito' | 'cheque' | 'mixto';
  concepto?: string;
  periodo_fiscal: string;
  cargado_marangatu: 'si' | 'no' | 'auto';
  notas?: string;
  sync_status: 'pending' | 'synced' | 'conflict';
  device_id?: string;
  created_at: string;
  updated_at: string;
  deleted_at?: string;
}

export interface ImputacionFiscalLocal {
  id: string;
  comprobante_id: string;
  categoria_irp_id: string;
  imputa_iva_credito: boolean;
  iva_credito_porcentaje: number;
  iva_credito_monto: number;
  imputa_irp: boolean;
  destino_reg_comprobante: 'IVA' | 'IRP-RSP' | 'NO_IMPUTAR';
  a_nombre_de?: string;
  rectificado: boolean;
  fecha_rectificacion?: string;
  notas_rectificacion?: string;
  created_at: string;
  updated_at: string;
}

export interface ArchivoAdjuntoLocal {
  id: string;
  comprobante_id: string;
  nombre_archivo: string;
  tipo_mime: string;
  tamano_bytes: number;
  blob?: Blob;
  ruta_almacenamiento?: string;
  hash_sha256?: string;
  sync_status: 'pending' | 'synced' | 'conflict';
  created_at: string;
}

export interface IngresoLocal {
  id: string;
  comprobante_id?: string;
  contacto_id: string;
  tipo_ingreso: 'salario' | 'aguinaldo' | 'vacaciones' | 'liquidacion_final' | 'honorarios' | 'otros';
  periodo_devengado: string;
  fecha_percepcion: string;
  monto_bruto: number;
  aporte_ips_trabajador: number;
  otros_descuentos: number;
  monto_exonerado: number;
  monto_computable_irp: number;
  es_gravado_irp: boolean;
  acumulado_anual?: number;
  notas?: string;
  sync_status: 'pending' | 'synced' | 'conflict';
  device_id?: string;
  created_at: string;
  updated_at: string;
  deleted_at?: string;
}

export interface CategoriaIRPLocal {
  id: string;
  codigo: string;
  nombre: string;
  descripcion?: string;
  articulo_ley?: string;
  limite_porcentaje?: number;
  activo: boolean;
  orden: number;
  imputa_iva_credito: boolean;
  iva_credito_porcentaje?: number;
  imputa_irp: boolean;
  destino_reg_comprobante: string;
}

export interface SyncQueueItem {
  autoId?: number;
  tabla: string;
  registro_id: string;
  operacion: 'create' | 'update' | 'delete';
  payload: unknown;
  timestamp: string;
  intentos: number;
  ultimo_error?: string;
}

export interface SyncMetadata {
  key: string;
  device_id: string;
  last_pull_timestamp: string | null;
  last_push_timestamp: string | null;
}

export class TributarioDatabase extends Dexie {
  contactos!: Table<ContactoLocal>;
  comprobantes!: Table<ComprobanteLocal>;
  imputaciones!: Table<ImputacionFiscalLocal>;
  adjuntos!: Table<ArchivoAdjuntoLocal>;
  ingresos!: Table<IngresoLocal>;
  categorias_irp!: Table<CategoriaIRPLocal>;
  sync_queue!: Table<SyncQueueItem>;
  sync_metadata!: Table<SyncMetadata>;

  constructor() {
    super('tributario_py');
    this.version(1).stores({
      contactos: 'id, ruc, tipo, sync_status',
      comprobantes: 'id, contacto_id, periodo_fiscal, tipo_operacion, fecha_emision, sync_status',
      imputaciones: 'id, comprobante_id, categoria_irp_id',
      adjuntos: 'id, comprobante_id, sync_status',
      ingresos: 'id, contacto_id, tipo_ingreso, periodo_devengado, sync_status',
      categorias_irp: 'id, codigo',
      sync_queue: '++autoId, tabla, registro_id, operacion, timestamp',
    });
    this.version(2).stores({
      sync_metadata: 'key',
    });
  }
}

export const db = new TributarioDatabase();
