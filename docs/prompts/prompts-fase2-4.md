# docs/prompts-fase2-4.md — Prompts para Claude Code

Prompts concisos por bloque. Claude Code tiene contexto completo en CLAUDE.md, docs/erd.md y docs/especificacion_tecnica.md — no repetir lo que ya está ahí.

---

## Fase 2 — Frontend PWA

### Bloque 2.2 — Layout y navegación

Mobile-first shell con bottom navigation. 5 tabs: Inicio, Comprobantes, Ingresos, Contactos, Reportes. Layout responsive: bottom nav en mobile, sidebar en desktop (md+). Usar Zustand para estado de navegación si hace falta. Cada tab es una ruta de React Router. Todas las páginas son placeholder por ahora (título + "En construcción").

### Bloque 2.3 — Pantallas CRUD

Implementar contra IndexedDB (Dexie), no contra la API. La API se conecta en Fase 3 con sync.

**Comprobantes:**
- Lista con filtros: período, tipo operación, contacto. Orden por fecha desc.
- Formulario de carga: contacto (selector/autocomplete por RUC o nombre), tipo comprobante, timbrado, número, fecha, montos desglosados (exento, gravado 5%, gravado 10% — IVA se calcula automático), total (se calcula automático), categoría IRP (selector que carga desde IndexedDB), la imputación se sugiere automáticamente según ReglaImputacion de la categoría seleccionada. El usuario puede override manual.
- Adjuntar foto/PDF (guardar blob en IndexedDB con sync_status pending).
- Editar, soft delete.

**Contactos:**
- Lista con búsqueda por RUC o nombre.
- Formulario: RUC, razón social, nombre fantasía, tipo, teléfono, email. Marcar como frecuente.

**Ingresos:**
- Lista filtrable por año y tipo.
- Formulario: tipo ingreso, contacto (empleador), período devengado, fecha percepción, monto bruto, aporte IPS (default 9% del bruto, editable), monto exonerado, monto computable (calculado). Mostrar acumulado anual en tiempo real.

Todos los formularios guardan en IndexedDB con `sync_status: 'pending'` y `id: crypto.randomUUID()`.

### Bloque 2.4 — Cámara y flujo rápido

Botón flotante "+" en pantalla de comprobantes → abre cámara (o galería). Después de capturar/seleccionar imagen → abre formulario de carga con la imagen ya adjunta. Flujo optimizado para: foto → llenar montos → elegir categoría → guardar. Máximo 3 taps después de la foto.

### Bloque 2.5 — Dashboard y reportes

Instalar Recharts. Pantalla Inicio = dashboard con:
- Resumen del mes actual (comprobantes cargados, IVA débito/crédito, saldo)
- Gráfico de barras: IVA mensual del año (débito vs crédito)
- Gráfico circular: egresos por categoría IRP del año
- Proyección IRP anual (ingresos - egresos = renta neta → impuesto estimado)
- Alertas: próximos vencimientos (F120 día 25, Reg. Comprob. día 26)

Datos desde IndexedDB. Los cálculos de IRP usan la escala progresiva de ConfiguracionFiscal (ver docs/erd.md tabla 10).

---

## Fase 3 — Sincronización

### Bloque 3.1 — Sync engine frontend

Implementar en `src/services/sync.ts` según docs/especificacion_tecnica.md sección 2. Sync queue en Dexie (tabla sync_queue). Push al recuperar conexión + cada 5 min + manual. Pull desde el backend con `?since=` timestamp. Backoff exponencial en errores (max 5 reintentos). Navigator.onLine para detectar conexión.

### Bloque 3.2 — Endpoints de sync backend

Implementar en backend según docs/especificacion_tecnica.md sección 1.11:
- POST `/api/v1/sync/push` — recibe cambios del cliente, aplica last-write-wins
- GET `/api/v1/sync/pull?since=` — devuelve registros modificados desde timestamp
- GET `/api/v1/sync/status` — estado de última sync

### Bloque 3.3 — Sync de adjuntos

Adjuntos se sincronizan por separado (multipart). Después de push de datos, el sync engine envía archivos pendientes via POST `/api/v1/comprobantes/:id/adjuntos`. Pull de adjuntos: solo metadata, blob bajo demanda.

### Bloque 3.4 — UI de sync

Indicador en el shell: ícono de sync con estado (synced/syncing/error/offline). Toast al completar sync o al fallar. Botón "Sincronizar ahora" en settings o pull-to-refresh. Lista de items con error de sync (retry manual por item).

---

## Fase 4 — Exportación y validación

### Bloque 4.1 — CSV Reg. Comprobantes

Endpoint ya existe en backend (Fase 1). Agregar botón en frontend: "Exportar Reg. Comprobantes" por período → llama al endpoint → descarga CSV. Verificar formato contra plantilla actual de Marangatu antes de dar por cerrado.

### Bloque 4.2 — Resumen F120

Endpoint ya existe. Agregar pantalla/modal que muestre el resumen del F120 para un período, con botón de copiar valores o exportar.

### Bloque 4.3 — Resumen F515

Endpoint ya existe. Agregar pantalla de consolidación anual IRP: ingresos por tipo, egresos por categoría, renta neta, impuesto calculado.

### Bloque 4.4 — Validaciones pre-presentación

Antes de exportar, correr validaciones: comprobantes sin categoría IRP, períodos con 0 comprobantes, montos que no cuadran (total ≠ exento + gravado_5 + iva_5 + gravado_10 + iva_10). Mostrar lista de warnings/errores.

### Bloque 4.5 — Backup

Endpoint backend que genera ZIP con todos los PDFs/fotos de un año. Botón en frontend para descargar.
