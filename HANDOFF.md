# HANDOFF.md — Estado actual operativo

Memoria operativa del proyecto. Leer esto primero al retomar después de una pausa.

**Última actualización:** 2026-05-09 — Bloque 1.6 completo. Fase 1 cerrada.

---

## Fase actual

**Fase 1 — Backend core (modelos + API + seed)**

Progreso:

- [x] **Bloque 1.1 — Setup inicial**
  - [x] Crear estructura de carpetas
  - [x] Docker Compose para PostgreSQL
  - [x] Configuración FastAPI + SQLAlchemy async + Alembic
  - [x] `.env` con variables base
- [x] **Bloque 1.2 — Modelos y migración**
  - [x] Modelos SQLAlchemy (10 tablas según ERD)
  - [x] Enums PostgreSQL nativos (13 tipos)
  - [x] Migración inicial Alembic (revision: e90319e232bb)
  - [x] Ciclo upgrade/downgrade/upgrade validado
- [x] **Bloque 1.3 — Seed data**
  - [x] Categorías IRP (16 categorías)
  - [x] Reglas de imputación por categoría
  - [x] Configuración fiscal 2025 y 2026
- [x] **Bloque 1.4 — API CRUD**
  - [x] Contactos (CRUD + búsqueda)
  - [x] Comprobantes + Imputación (creación atómica)
  - [x] Ingresos (CRUD + acumulado anual)
  - [x] Adjuntos (upload multipart)
  - [x] Períodos fiscales (listado + recálculo)
  - [x] Declaraciones juradas (registro)
  - [x] Imputaciones (rectificación individual + batch)
- [x] **Bloque 1.5 — Reportes y exportación**
  - [x] Dashboard resumen
  - [x] IVA mensual
  - [x] Proyección IRP
  - [x] Exportación CSV Reg. Comprobantes
  - [x] Exportación resumen F120 / F515
- [x] **Bloque 1.6 — Tests del backend** (29 tests, 100% pass)
  - [x] test_irp_calculo.py (9 unit tests, sin BD)
  - [x] test_comprobantes.py (7 integration tests)
  - [x] test_exportacion.py (7 integration tests)
  - [x] test_periodos.py (6 integration tests)

Detalle del roadmap en `docs/roadmap.md`.

---

## Estado BD local

- Alembic head: `e90319e232bb` (initial)
- 10 tablas creadas con 13 tipos ENUM nativos PostgreSQL
- Seed ejecutado: 16 categorias_irp, 16 reglas_imputacion, 2 configuracion_fiscal (2025/2026)
- **PENDIENTE**: actualizar `ruc`, `razon_social`, `ultimo_digito_ruc` en configuracion_fiscal (valores actuales = "COMPLETAR")

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
```

**pgAdmin**: pgAdmin corre en red `bridge` separada. `tributario_db` debe conectarse a `bridge` manualmente después de cada reinicio (paso 2). Usar IP directa, no nombre de contenedor (bridge default no tiene DNS entre contenedores).

---

## Próximo paso concreto

**Fase 1 completa.** Siguiente: **Fase 2 — Frontend PWA**

Ver detalle en `docs/roadmap.md`. Arrancar por:
1. Bloque 2.1 — Setup React + Vite + Tailwind + PWA manifest + Service Worker básico
2. Bloque 2.2 — IndexedDB con Dexie.js (esquema local espejo de PostgreSQL)


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
