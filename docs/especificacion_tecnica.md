# Especificación Técnica — App Tributaria Personal Paraguay

## 1. API REST — Endpoints

### Convenciones generales

- Base URL: `http://localhost:8000/api/v1`
- Autenticación: JWT simple (un solo usuario, pero preparado para futuro multi-usuario)
- Formato: JSON
- Paginación: `?page=1&per_page=50` (default 50, max 200)
- Filtros: query params. Ej: `?periodo=2026-04&tipo_operacion=compra`
- Orden: `?sort_by=fecha_emision&order=desc`
- Respuestas: `{ "data": {...}, "meta": {...} }` para singular, `{ "data": [...], "meta": { "total", "page", "per_page" } }` para listas
- Errores: `{ "error": { "code": "VALIDATION_ERROR", "message": "...", "details": [...] } }`
- Timestamps en respuestas: ISO 8601 con timezone (UTC)

---

### 1.1 Contactos

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/contactos` | Listar contactos. Filtros: `tipo`, `ruc`, `es_frecuente`, `q` (búsqueda texto) |
| GET | `/contactos/:id` | Detalle de un contacto |
| POST | `/contactos` | Crear contacto |
| PUT | `/contactos/:id` | Actualizar contacto |
| DELETE | `/contactos/:id` | Soft delete |

**POST/PUT body:**
```json
{
  "id": "uuid-generado-en-cliente",
  "ruc": "80012345-6",
  "razon_social": "Supermercados S.A.",
  "nombre_fantasia": "Super Eco",
  "tipo": "proveedor",
  "tipo_contribuyente": "persona_juridica",
  "telefono": "0971123456",
  "email": "contacto@supereco.com.py",
  "direccion": "Caacupé, Cordillera",
  "notas": "Proveedor frecuente de alimentación",
  "es_frecuente": true
}
```

---

### 1.2 Categorías IRP

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/categorias-irp` | Listar todas (incluye regla de imputación asociada) |
| GET | `/categorias-irp/:id` | Detalle |

Solo lectura. Se precargan con seed data. Si en el futuro se necesita editar, se agrega PUT.

**Respuesta GET incluye la regla embebida:**
```json
{
  "id": "...",
  "codigo": "ALIMENTACION",
  "nombre": "Alimentación",
  "articulo_ley": "Art. 64 num. 1",
  "regla_imputacion": {
    "imputa_iva_credito": false,
    "iva_credito_porcentaje": null,
    "imputa_irp": true,
    "destino_reg_comprobante": "IRP-RSP"
  }
}
```

---

### 1.3 Comprobantes

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/comprobantes` | Listar. Filtros: `periodo_fiscal`, `tipo_operacion`, `contacto_id`, `categoria_irp`, `cargado_marangatu`, `fecha_desde`, `fecha_hasta` |
| GET | `/comprobantes/:id` | Detalle (incluye imputación y adjuntos) |
| POST | `/comprobantes` | Crear comprobante con imputación |
| PUT | `/comprobantes/:id` | Actualizar |
| DELETE | `/comprobantes/:id` | Soft delete |

**POST body (comprobante + imputación en una sola request):**
```json
{
  "id": "uuid-cliente",
  "contacto_id": "uuid-contacto",
  "tipo_operacion": "compra",
  "tipo_comprobante": "factura",
  "forma_emision": "electronica",
  "numero_timbrado": "12345678",
  "numero_comprobante": "001-001-0000123",
  "fecha_emision": "2026-04-15",
  "fecha_percepcion": "2026-04-15",
  "condicion": "contado",
  "moneda": "PYG",
  "monto_exento": 0,
  "monto_gravado_5": 0,
  "iva_5": 0,
  "monto_gravado_10": 150000,
  "iva_10": 15000,
  "total": 165000,
  "forma_pago": "tarjeta_debito",
  "concepto": "Compras quincenales",
  "periodo_fiscal": "2026-04",
  "cargado_marangatu": "auto",
  "imputacion": {
    "categoria_irp_codigo": "ALIMENTACION",
    "imputa_iva_credito": false,
    "iva_credito_porcentaje": 0,
    "imputa_irp": true,
    "destino_reg_comprobante": "IRP-RSP",
    "a_nombre_de": "yo"
  }
}
```

**Nota**: La imputación se envía embebida en el comprobante para simplificar el flujo del frontend. El backend crea ambos registros en una transacción.

---

### 1.4 Archivos adjuntos

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/comprobantes/:id/adjuntos` | Subir archivo (multipart/form-data) |
| GET | `/comprobantes/:id/adjuntos` | Listar adjuntos de un comprobante |
| GET | `/adjuntos/:id/download` | Descargar archivo |
| DELETE | `/adjuntos/:id` | Eliminar adjunto |

**POST**: `multipart/form-data` con campo `archivo`. El backend calcula hash_sha256, almacena en `{STORAGE_PATH}/{año}/{mes}/{uuid}.{ext}` y devuelve el registro.

---

### 1.5 Ingresos

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/ingresos` | Listar. Filtros: `anio_fiscal`, `tipo_ingreso`, `contacto_id`, `fecha_desde`, `fecha_hasta` |
| GET | `/ingresos/:id` | Detalle |
| POST | `/ingresos` | Crear ingreso |
| PUT | `/ingresos/:id` | Actualizar |
| DELETE | `/ingresos/:id` | Soft delete |
| GET | `/ingresos/acumulado/:anio` | Acumulado anual con tracking del umbral 80M |

**POST body:**
```json
{
  "id": "uuid-cliente",
  "contacto_id": "uuid-empleador",
  "comprobante_id": null,
  "tipo_ingreso": "salario",
  "periodo_devengado": "2026-03",
  "fecha_percepcion": "2026-04-05",
  "monto_bruto": 8000000,
  "aporte_ips_trabajador": 720000,
  "otros_descuentos": 0,
  "monto_exonerado": 0,
  "monto_computable_irp": 7280000,
  "es_gravado_irp": true,
  "notas": "Sueldo marzo 2026"
}
```

**GET `/ingresos/acumulado/2026` respuesta:**
```json
{
  "anio_fiscal": 2026,
  "umbral_irp": 80000000,
  "acumulado_bruto": 45000000,
  "acumulado_computable_irp": 40950000,
  "porcentaje_umbral": 51.19,
  "superado_umbral": false,
  "fecha_cruce_umbral": null,
  "detalle_mensual": [
    { "mes": "2026-01", "computable": 7280000, "acumulado": 7280000 },
    { "mes": "2026-02", "computable": 7280000, "acumulado": 14560000 }
  ]
}
```

---

### 1.6 Imputaciones fiscales

| Método | Ruta | Descripción |
|---|---|---|
| PUT | `/imputaciones/:id` | Actualizar imputación (para rectificaciones) |
| PUT | `/imputaciones/batch-rectificar` | Rectificar múltiples imputaciones de un período |

**PUT batch body:**
```json
{
  "periodo_fiscal": "2026-01",
  "cambios": {
    "destino_anterior": "NO_IMPUTAR",
    "destino_nuevo": "IRP-RSP",
    "solo_categorias": ["ALIMENTACION", "VESTIMENTA", "ALQUILER_VIVIENDA"],
    "notas_rectificacion": "Aprobada inscripción IRP-RSP, reimputando egresos deducibles"
  }
}
```

Este endpoint existe porque necesitás rectificar en bloque cuando la DNIT apruebe tu IRP-RSP (cambiar NO_IMPUTAR → IRP-RSP en todos los egresos deducibles de enero-marzo 2026).

---

### 1.7 Períodos fiscales

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/periodos` | Listar períodos. Filtros: `anio_fiscal`, `f120_presentado`, `reg_comprobantes_presentado` |
| GET | `/periodos/:periodo` | Detalle con totales recalculados |
| POST | `/periodos/:periodo/recalcular` | Forzar recálculo de totales desde comprobantes |

**GET `/periodos/2026-04` respuesta:**
```json
{
  "periodo": "2026-04",
  "anio_fiscal": 2026,
  "resumen_iva": {
    "ventas_gravadas_10": 0,
    "ventas_gravadas_5": 0,
    "ventas_exentas": 0,
    "iva_debito": 0,
    "compras_gravadas_10": 1500000,
    "compras_gravadas_5": 1895000,
    "compras_exentas": 100000,
    "iva_credito_utilizado": 0,
    "saldo_iva": 0
  },
  "resumen_irp": {
    "ingresos_computables": 7280000,
    "egresos_por_categoria": {
      "ALIMENTACION": 1200000,
      "ALQUILER_VIVIENDA": 1895000,
      "VEHICULO": 350000,
      "SERVICIOS_BASICOS": 180000
    },
    "total_egresos": 3625000
  },
  "estado_presentacion": {
    "f120_presentado": false,
    "f120_vencimiento": "2026-05-25",
    "f120_dias_restantes": 16,
    "reg_comprobantes_presentado": false,
    "reg_comprobantes_vencimiento": "2026-05-26",
    "reg_comprobantes_dias_restantes": 17
  },
  "comprobantes": {
    "compras": 35,
    "ventas": 0
  }
}
```

---

### 1.8 Declaraciones juradas

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/declaraciones` | Listar. Filtros: `formulario`, `anio_fiscal`, `estado` |
| POST | `/declaraciones` | Registrar DJ presentada |
| PUT | `/declaraciones/:id` | Actualizar (ej: agregar fecha de pago) |

---

### 1.9 Reportes y dashboard

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/reportes/dashboard` | Resumen general del año fiscal actual |
| GET | `/reportes/iva-mensual/:anio` | IVA débito/crédito/saldo por mes |
| GET | `/reportes/irp-proyeccion/:anio` | Proyección IRP: ingresos, egresos por categoría, renta neta, impuesto estimado |
| GET | `/reportes/flujo-caja/:anio` | Ingresos vs egresos mensual |
| GET | `/reportes/vencimientos` | Próximos vencimientos de DJ con estado |
| GET | `/reportes/egresos-por-categoria/:anio` | Desglose de egresos por categoría IRP |

**GET `/reportes/irp-proyeccion/2026` respuesta:**
```json
{
  "anio_fiscal": 2026,
  "ejercicio": { "inicio": "2026-01-01", "fin": "2026-12-31" },
  "ingresos_brutos_acumulados": 45000000,
  "ingresos_computables_irp": 40950000,
  "egresos_deducibles_acumulados": 22000000,
  "egresos_por_categoria": {
    "ALIMENTACION": 8500000,
    "ALQUILER_VIVIENDA": 9475000,
    "VEHICULO": 1200000,
    "SERVICIOS_BASICOS": 900000,
    "ESPARCIMIENTO": 400000,
    "ACTIVIDAD_GRAVADA": 1525000
  },
  "renta_neta_actual": 18950000,
  "renta_neta_proyectada_anual": 29000000,
  "impuesto_proyectado": {
    "tramo_8_porciento": { "base": 29000000, "impuesto": 2320000 },
    "tramo_9_porciento": { "base": 0, "impuesto": 0 },
    "tramo_10_porciento": { "base": 0, "impuesto": 0 },
    "total": 2320000
  },
  "reserva_mensual_sugerida": 193333,
  "meses_restantes": 8
}
```

---

### 1.10 Exportación

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/exportar/reg-comprobantes/:periodo` | Genera CSV para carga masiva en Marangatu |
| GET | `/exportar/f120-resumen/:periodo` | Resumen pre-armado para llenar F120 manualmente |
| GET | `/exportar/f515-resumen/:anio` | Resumen anual pre-armado para F515 |
| GET | `/exportar/comprobantes-backup/:anio` | ZIP con todos los PDFs/fotos del año |

---

### 1.11 Sincronización

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/sync/push` | Enviar cambios del cliente al server |
| GET | `/sync/pull` | Obtener cambios del server desde timestamp |
| GET | `/sync/status` | Estado de la última sincronización |

Detallado en sección 2.

---

### 1.12 Configuración fiscal

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/configuracion/:anio` | Configuración del año fiscal |
| PUT | `/configuracion/:anio` | Actualizar (si cambian parámetros) |
| POST | `/configuracion` | Crear configuración para nuevo año fiscal |

---

## 2. Flujo de sincronización offline → backend

### 2.1 Estrategia general

**Last-write-wins con timestamps** — adecuado para un solo usuario con dos dispositivos (celular + PC).

### 2.2 Almacenamiento offline (IndexedDB)

El frontend mantiene en IndexedDB las mismas tablas que PostgreSQL, más una tabla de control:

**`sync_queue`** — cola de cambios pendientes:
```
{
  id: uuid,
  tabla: "comprobantes",
  registro_id: uuid,
  operacion: "create" | "update" | "delete",
  payload: { ...datos completos },
  timestamp: ISO8601,
  intentos: 0,
  ultimo_error: null
}
```

**`sync_metadata`** — estado de sincronización:
```
{
  last_pull_timestamp: ISO8601,    // última vez que se descargaron cambios del server
  last_push_timestamp: ISO8601,    // última vez que se enviaron cambios al server
  device_id: "uuid-dispositivo"
}
```

### 2.3 Flujo de escritura (offline-first)

1. El usuario crea/edita un registro en el celular
2. Se guarda inmediatamente en IndexedDB con `sync_status: "pending"`
3. Se agrega una entrada a `sync_queue`
4. Si hay conexión → se intenta push inmediato
5. Si no hay conexión → queda encolado hasta reconexión

### 2.4 Push (cliente → servidor)

**POST `/sync/push`**

```json
{
  "device_id": "uuid-dispositivo",
  "cambios": [
    {
      "tabla": "comprobantes",
      "registro_id": "uuid",
      "operacion": "create",
      "payload": { ... },
      "timestamp": "2026-05-09T14:30:00Z"
    },
    {
      "tabla": "imputaciones_fiscales",
      "registro_id": "uuid",
      "operacion": "update",
      "payload": { ... },
      "timestamp": "2026-05-09T14:30:01Z"
    }
  ]
}
```

**Respuesta del server:**
```json
{
  "aceptados": ["uuid1", "uuid2"],
  "rechazados": [],
  "conflictos": [],
  "server_timestamp": "2026-05-09T14:30:05Z"
}
```

**Resolución de conflictos**: Como sos un solo usuario, los conflictos reales son raros. Si el mismo registro fue editado desde PC y celular entre syncs, gana el `updated_at` más reciente. El server devuelve el registro ganador en `conflictos` para que el cliente actualice su IndexedDB.

### 2.5 Pull (servidor → cliente)

**GET `/sync/pull?since=2026-05-09T10:00:00Z`**

El server devuelve todos los registros modificados desde ese timestamp:

```json
{
  "cambios": {
    "contactos": [ { ...registros modificados } ],
    "comprobantes": [ ... ],
    "imputaciones_fiscales": [ ... ],
    "ingresos": [ ... ]
  },
  "server_timestamp": "2026-05-09T14:30:05Z",
  "hay_mas": false
}
```

El cliente aplica los cambios a IndexedDB y actualiza `last_pull_timestamp`.

### 2.6 Sincronización de archivos adjuntos

Los archivos son el caso especial — son pesados y no caben bien en JSON.

1. **Offline**: El celular guarda el blob en IndexedDB (limitado por storage del browser, típicamente ~100MB es seguro)
2. **Push**: Los archivos se envían por separado vía `POST /comprobantes/:id/adjuntos` (multipart)
3. **Pull**: El cliente solo descarga la metadata (nombre, tipo, tamaño). El blob se descarga bajo demanda con `GET /adjuntos/:id/download`
4. **En `sync_queue`**: Los adjuntos pendientes se envían después de sus comprobantes padre

### 2.7 Triggers automáticos de sync

- **Al recuperar conexión**: push de toda la cola pendiente
- **Cada 5 minutos** (si hay conexión): pull de cambios
- **Al abrir la app**: pull + push
- **Manual**: botón "Sincronizar ahora" en la UI

### 2.8 Manejo de errores

- Cada entrada en `sync_queue` tiene un contador de `intentos`
- Máximo 5 reintentos con backoff exponencial (1s, 5s, 15s, 30s, 60s)
- Si falla 5 veces → se marca como error y se muestra al usuario
- El usuario puede reintentar manualmente o descartar

---

## 3. Formatos de exportación

### 3.1 CSV para carga masiva de Registro de Comprobantes (Marangatu)

Marangatu permite importar comprobantes vía CSV. El formato esperado (basado en RG 90/2021 y la plantilla de carga masiva del sistema):

**Archivo: `reg_comprobantes_{periodo}.csv`**

Columnas separadas por punto y coma (`;`):

```csv
tipo_registro;tipo_comprobante;fecha_emision;ruc_contraparte;nombre_contraparte;numero_timbrado;numero_comprobante;monto_gravado_10;iva_10;monto_gravado_5;iva_5;monto_exento;total;condicion;tipo_operacion;imputacion
```

Valores posibles (según Marangatu):

- `tipo_registro`: `C` (compra), `V` (venta)
- `tipo_comprobante`: `1` (factura), `2` (nota crédito), `3` (nota débito), `4` (autofactura), `5` (boleta venta), `6` (ticket), `7` (boleta RESIMPLE)
- `fecha_emision`: `DD/MM/YYYY`
- `condicion`: `1` (contado), `2` (crédito)
- `imputacion`: `211` (IVA), `715` (IRP-RSP), `0` (NO IMPUTAR)

**Ejemplo de línea:**
```
C;1;15/04/2026;80012345-6;Supermercados S.A.;12345678;001-001-0000123;150000;15000;0;0;0;165000;1;C;715
```

**NOTA IMPORTANTE**: Este formato debe verificarse contra la plantilla actual de Marangatu al momento de implementar. La DNIT puede modificar el formato sin previo aviso. El endpoint debe generar el CSV y retornarlo como descarga.

### 3.2 Resumen pre-armado para F120

No es un archivo para importar — es un JSON/PDF con los totales que el usuario necesita para llenar el F120 manualmente en Marangatu.

**Estructura:**
```json
{
  "periodo": "2026-04",
  "ruc": "5424529-0",
  "formulario": "F120",
  "ventas": {
    "gravadas_10": 0,
    "iva_debito_10": 0,
    "gravadas_5": 0,
    "iva_debito_5": 0,
    "exentas": 0,
    "total_iva_debito": 0
  },
  "compras": {
    "gravadas_10": 1500000,
    "iva_credito_10_utilizado": 0,
    "gravadas_5": 1895000,
    "iva_credito_5_utilizado": 0,
    "exentas": 100000,
    "total_iva_credito_utilizado": 0
  },
  "liquidacion": {
    "iva_debito": 0,
    "iva_credito": 0,
    "saldo": 0,
    "a_pagar": 0,
    "saldo_a_favor": 0
  }
}
```

### 3.3 Resumen pre-armado para F515 (IRP anual)

**Estructura:**
```json
{
  "anio_fiscal": 2026,
  "ruc": "5424529-0",
  "formulario": "F515",
  "ejercicio": {
    "inicio": "2026-01-01",
    "fin": "2026-12-31"
  },
  "ingresos": {
    "salarios_brutos": 96000000,
    "aporte_ips": 8640000,
    "aguinaldo_exonerado": 8000000,
    "honorarios_profesionales": 990850,
    "otros_ingresos": 0,
    "total_computable_irp": 88350850
  },
  "egresos_deducibles": {
    "ALIMENTACION": { "total": 18000000, "cantidad_comprobantes": 120 },
    "ALQUILER_VIVIENDA": { "total": 22740000, "cantidad_comprobantes": 12 },
    "VESTIMENTA": { "total": 3500000, "cantidad_comprobantes": 8 },
    "VEHICULO": { "total": 5000000, "cantidad_comprobantes": 36 },
    "SERVICIOS_BASICOS": { "total": 2400000, "cantidad_comprobantes": 12 },
    "SALUD": { "total": 1500000, "cantidad_comprobantes": 6 },
    "ESPARCIMIENTO": { "total": 2000000, "cantidad_comprobantes": 15 },
    "ACTIVIDAD_GRAVADA": { "total": 3600000, "cantidad_comprobantes": 12 },
    "SERVICIOS_FINANCIEROS": { "total": 800000, "cantidad_comprobantes": 12 },
    "APORTE_IPS": { "total": 8640000, "cantidad_comprobantes": 12 }
  },
  "total_egresos_deducibles": 68180000,
  "renta_neta": 20170850,
  "liquidacion_irp": {
    "tramo_8": { "base": 20170850, "impuesto": 1613668 },
    "tramo_9": { "base": 0, "impuesto": 0 },
    "tramo_10": { "base": 0, "impuesto": 0 },
    "total_impuesto": 1613668,
    "retenciones_sufridas": 0,
    "saldo_a_pagar": 1613668
  }
}
```

---

## 4. Estructura de carpetas del proyecto

```
tributario-py/
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app, CORS, middleware
│   │   ├── config.py                  # Settings (pydantic-settings)
│   │   ├── database.py                # Engine, session factory
│   │   ├── models/                    # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── contacto.py
│   │   │   ├── categoria_irp.py
│   │   │   ├── regla_imputacion.py
│   │   │   ├── comprobante.py
│   │   │   ├── archivo_adjunto.py
│   │   │   ├── imputacion_fiscal.py
│   │   │   ├── ingreso.py
│   │   │   ├── periodo_fiscal.py
│   │   │   ├── declaracion_jurada.py
│   │   │   ├── configuracion_fiscal.py
│   │   │   └── mixins.py             # TimestampMixin, SyncMixin, SoftDeleteMixin
│   │   ├── schemas/                   # Pydantic v2 schemas
│   │   │   ├── __init__.py
│   │   │   ├── contacto.py
│   │   │   ├── comprobante.py
│   │   │   ├── ingreso.py
│   │   │   ├── imputacion.py
│   │   │   ├── periodo.py
│   │   │   ├── declaracion.py
│   │   │   ├── reportes.py
│   │   │   ├── sync.py
│   │   │   └── exportacion.py
│   │   ├── api/                       # Routers
│   │   │   ├── __init__.py
│   │   │   ├── contactos.py
│   │   │   ├── comprobantes.py
│   │   │   ├── adjuntos.py
│   │   │   ├── ingresos.py
│   │   │   ├── imputaciones.py
│   │   │   ├── periodos.py
│   │   │   ├── declaraciones.py
│   │   │   ├── reportes.py
│   │   │   ├── exportacion.py
│   │   │   ├── sync.py
│   │   │   └── configuracion.py
│   │   ├── services/                  # Lógica de negocio
│   │   │   ├── __init__.py
│   │   │   ├── comprobante_service.py
│   │   │   ├── imputacion_service.py
│   │   │   ├── ingreso_service.py
│   │   │   ├── periodo_service.py     # Recálculo de totales
│   │   │   ├── irp_service.py         # Cálculo IRP progresivo
│   │   │   ├── exportacion_service.py # Generación CSV/JSON
│   │   │   ├── sync_service.py
│   │   │   └── storage_service.py     # Manejo de archivos
│   │   └── seed/                      # Datos iniciales
│   │       ├── __init__.py
│   │       ├── categorias_irp.py
│   │       ├── reglas_imputacion.py
│   │       └── configuracion_2025_2026.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_comprobantes.py
│   │   ├── test_irp_calculo.py
│   │   ├── test_exportacion.py
│   │   └── test_sync.py
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── .env.example
├── frontend/
│   ├── public/
│   │   ├── manifest.json              # PWA manifest
│   │   ├── sw.js                      # Service Worker
│   │   └── icons/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   │   ├── api.js                 # HTTP client (fetch wrapper)
│   │   │   ├── db.js                  # IndexedDB wrapper (Dexie.js)
│   │   │   └── sync.js               # Motor de sincronización
│   │   ├── stores/                    # Estado global (Zustand o similar)
│   │   └── utils/
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── package.json
├── docker-compose.yml                 # PostgreSQL + backend para dev local
├── README.md
└── docs/
    ├── erd.md
    └── api.md
```

---

## 5. Stack técnico confirmado

### Backend
- **Python 3.12+**
- **FastAPI** — framework web
- **Pydantic v2** — validación y schemas
- **SQLAlchemy 2.0** — ORM (async con asyncpg)
- **Alembic** — migraciones
- **PostgreSQL 16** — base de datos
- **python-multipart** — upload de archivos
- **pydantic-settings** — configuración desde .env
- **uvicorn** — ASGI server

### Frontend
- **React 18** — UI
- **Vite** — bundler
- **Tailwind CSS** — estilos
- **Dexie.js** — wrapper de IndexedDB (simplifica CRUD offline)
- **Recharts** — gráficos para reportes
- **Workbox** — Service Worker toolkit (caching, background sync)
- **React Router** — navegación
- **Zustand** — estado global ligero

### Infraestructura local
- **Docker Compose** — PostgreSQL containerizado
- **Uvicorn** — backend corriendo directo o en Docker
- **Vite dev server** — frontend en desarrollo
- Los dispositivos acceden vía IP local de la PC (ej: `http://192.168.1.100:5173`)
