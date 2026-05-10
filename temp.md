Prueba A — Push básico (comprobante + imputación)

Abrir DevTools → Application → IndexedDB → tributario_py
Crear un comprobante nuevo en el formulario y guardar
Verificar en sync_queue: deben aparecer 2 ítems — uno con tabla: comprobantes y otro con tabla: imputaciones_fiscales
Si el backend está corriendo, el SyncIndicator mostrará "Sincronizando..." y luego pasará a idle
Verificar en sync_queue: tabla vacía (ambos aceptados)
Verificar en backend: GET /api/v1/comprobantes → aparece el comprobante. GET /api/v1/comprobantes/{id}/imputacion → aparece la imputación
Prueba B — Offline → Online

DevTools → Network → "Offline"
Crear un comprobante — sync_queue tiene 2 ítems, sync_status: pending en Dexie
Network → "Online" — push se dispara automáticamente (evento online)
Verificar que sync_queue queda vacía y el backend recibió ambos registros
Prueba C — Pull

Crear un contacto directamente via POST /api/v1/contactos en Swagger (localhost:8000/docs)
Esperar 5 minutos (pull interval) o clickar "Sincronizar ahora" en el SyncIndicator
Verificar en IndexedDB → contactos: aparece el registro con sync_status: synced
Prueba D — Adjunto

Crear comprobante con foto adjunta
sync_queue: deben aparecer 3 ítems — comprobante, imputación, adjunto
Al sincronizar: comprobante e imputación se pushean primero; adjunto se envía via multipart solo si comprobante.sync_status === 'synced'
Verificar en GET /api/v1/comprobantes/{id}/adjuntos
Prueba E — Retry manual

Bajar el backend (Ctrl+C)
Crear un comprobante — items en sync_queue, intentos: 0
Esperar backoffs (1s, 5s, 15s...) — ver intentos incrementar en Dexie
SyncIndicator muestra rojo con "↩ Reintentar"
Levantar backend → clickar Reintentar → se limpia la cola
