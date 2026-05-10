# HANDOFF.md — Estado actual operativo

Memoria operativa del proyecto. Leer esto primero al retomar después de una pausa.

**Última actualización:** 2026-05-10 — Fase 3 completa. Fase 4 pendiente.

---

## Fase actual

**Fase 4 — Exportación y validación** (no iniciada)

Ver puntos de arranque en la sección "Próximo paso concreto".

---

## Fase 3 — Sincronización (cerrada)

- [x] **Bloque 3.1 — Sync engine en frontend** (cola de cambios, push/pull, backoff exponencial)
- [x] **Bloque 3.2 — Endpoints de sync en backend** (push, pull, status)
- [x] **Bloque 3.3 — Sync de archivos adjuntos** (multipart, separado de datos)
- [x] **Bloque 3.4 — UI de estado de sync** (indicador, errores, retry manual)
- [x] **Testing de integración + fixes** (ver notas abajo)

### Fixes aplicados en testing de integración

- `useComprobantes`: `pushSync()` ahora también envía `ImputacionFiscal` a `sync_queue` en crear y actualizar.
- `sync.ts`: `pull()` silencia errores de red (evita que `syncAll()` quede colgado en estado `'syncing'`).
- `sync.ts`: el intervalo de 5 min llama `syncAll()` en lugar de solo `pull()`, para que también haga push.
- `sync.ts`: `pushSync()` dispara `push()` fire-and-forget al guardar un registro (push inmediato sin esperar el intervalo).
- `sync.ts`: `cleanupLocalCache()` corre al final de cada `syncAll()` — borra blobs de adjuntos sincronizados y elimina de Dexie los registros con `deleted_at` ya confirmados en el servidor.
- `SyncIndicator.tsx`: panel compact usa `right-0` (se abría fuera de pantalla en mobile).
- `adjuntos.py`: el endpoint de upload acepta `adjunto_id` via Form para respetar el UUID generado en el cliente.
- `ComprobanteForm.tsx`: vista de adjuntos existentes en modo edición (miniatura, ícono PDF, borrar).
- `ComprobanteForm.tsx`: reconciliación con backend al abrir en edición — elimina de Dexie adjuntos que ya no existen en el servidor.
- `ComprobanteForm.tsx`: recarga la lista de adjuntos cuando `lastSyncAt` cambia (limpia cache visual post-sync).

---

## Fase 2 — Frontend PWA (cerrada)

- [x] **Bloque 2.1** — Setup Vite 5 + React 18 + Tailwind + PWA manifest + SW básico + Dexie (7 tablas)
- [x] **Bloque 2.2** — Layout y navegación (AppLayout, BottomNav, Sidebar, 5 rutas)
- [x] **Bloque 2.3** — CRUD completo: Contactos, Comprobantes, Ingresos. Hooks Dexie, formularios con autocomplete, adjunto blob, sync_queue, transacción atómica comprobante + imputación
- [x] **Bloque 2.4** — Flujo offline: file picker + cámara en ComprobanteForm, vista previa blob, navegación con `pendingFile` desde lista
- [x] **Bloque 2.5** — Dashboard (`Home.tsx`): alertas vencimientos, métricas del mes, BarChart IVA mensual, PieChart egresos × categoría, proyección IRP con escala progresiva. Alertas muestran el vencimiento más próximo por tipo (período anterior vence este mes; si ya pasó, muestra el del período actual), ventana 45 días.

---

## Fase 1 — Backend core (cerrada)

- [x] **Bloque 1.1 — Setup inicial**
- [x] **Bloque 1.2 — Modelos y migración** (revision: e90319e232bb)
- [x] **Bloque 1.3 — Seed data** (16 categorías IRP, reglas, config fiscal 2025/2026)
- [x] **Bloque 1.4 — API CRUD** (contactos, comprobantes, ingresos, adjuntos, períodos, DJ, imputaciones)
- [x] **Bloque 1.5 — Reportes y exportación** (dashboard, IVA mensual, proyección IRP, CSV, F120/F515)
- [x] **Bloque 1.6 — Tests del backend** (29 tests, 100% pass)

Detalle del roadmap en `docs/roadmap.md`.

---

## Estado BD local

- Alembic head: `e90319e232bb` (initial)
- 10 tablas creadas con 13 tipos ENUM nativos PostgreSQL
- Seed ejecutado: 16 categorias_irp, 16 reglas_imputacion, 2 configuracion_fiscal (2025/2026)

---

## Variables de entorno (.env local)

```
DATABASE_URL=postgresql+asyncpg://admin:admin123@localhost:5432/tributario_py
STORAGE_PATH=./storage
```

---

## Arranque del entorno local

```powershell
# 1. PostgreSQL en Docker (desde la raíz del proyecto)
docker compose up -d

# 2. Conectar tributario_db a la red bridge para pgAdmin
#    (necesario cada vez que se reinicia el contenedor)
docker network connect bridge tributario_db

# 3. IP para pgAdmin (puede cambiar si se recrean contenedores)
docker inspect tributario_db | Select-String '"IPAddress"'
#    Usar la IP 172.17.x.x en pgAdmin → host, port 5432, db tributario_py, user admin

# 4. Venv + FastAPI (desde backend/)
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --reload

# 5. Migración
alembic upgrade head

# 6. Seed
python -m app.seed.run

# 7. Frontend (desde frontend/)
cd ..\frontend
npm run dev
```

**pgAdmin**: pgAdmin corre en red `bridge` separada. `tributario_db` debe conectarse a `bridge` manualmente después de cada reinicio (paso 2). Usar IP directa, no nombre de contenedor (bridge default no tiene DNS entre contenedores).

---

## Próximo paso concreto

**Fase 4 — Exportación.** Puntos de arranque:
- `Reportes.tsx` es el placeholder — habilitar exportación CSV Reg. Comprobantes, resumen F120/F515, validaciones pre-presentación.
- Endpoints backend ya existen en `api/exportacion.py` (Bloque 1.5).
- `src/stores/syncStore.ts` — Zustand store ya disponible, puede usarse para estado global de reportes si se necesita.

**Nota sobre `pages/Reportes.tsx`:** actualmente muestra "En construcción". Es el placeholder para Fase 4 (exportación CSV Reg. Comprobantes, resumen F120/F515, validaciones pre-presentación). No eliminar ni reutilizar para otra cosa.

---

## Documentación del proyecto

| Archivo                          | Para qué                    | Frecuencia de cambio |
| -------------------------------- | --------------------------- | -------------------- |
| `CLAUDE.md`                      | Reglas activas del proyecto | Bajo                 |
| `HANDOFF.md` (este)              | Estado operativo actual     | Alto                 |
| `docs/roadmap.md`                | Fases y bloques             | Bajo                 |
| `docs/design-decisions.md`       | Historial de por qué        | Bajo                 |
| `docs/common-patterns.md`        | Patrones de código          | Bajo                 |
| `docs/erd.md`                    | Modelo de datos detallado   | Bajo                 |
| `docs/especificacion_tecnica.md` | API, sync, exportación      | Bajo                 |
| `docs/comandos.md`               | Referencia de comandos      | Bajo                 |

---

## Cómo retomar después de pausa

1. Leer este archivo (HANDOFF.md) primero
2. `git log --oneline -20` para ver últimos commits
3. Verificar entorno local: `docker ps`, venv activado, `alembic current`
4. Levantar backend: `uvicorn app.main:app --reload`
5. Abrir Claude Code en la raíz del proyecto
