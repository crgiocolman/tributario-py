# HANDOFF.md — Estado actual operativo

Memoria operativa del proyecto. Leer esto primero al retomar después de una pausa.

**Última actualización:** 2026-05-10 — Bloque 2.2 completo. Fase 2 en curso.

---

## Fase actual

**Fase 2 — Frontend PWA**

Progreso:

- [x] **Bloque 2.1 — Setup frontend PWA**
  - [x] Vite 5 + React 18 + TypeScript (Vite 5 por compatibilidad con Node 20.12.1)
  - [x] Tailwind CSS via `@tailwindcss/vite`
  - [x] Proxy `/api` → `http://localhost:8000` en `vite.config.ts`
  - [x] `public/manifest.json` + `<link rel="manifest">` en `index.html`
  - [x] `public/sw.js` básico registrado en `main.tsx`
  - [x] Estructura de carpetas: `components/`, `pages/`, `hooks/`, `services/`, `stores/`, `utils/`, `types/`
  - [x] `src/services/db.ts` — schema Dexie completo (7 tablas, espejo del ERD)
  - [x] `src/services/api.ts` — fetch wrapper tipado
  - [x] `src/services/sync.ts` — placeholder Fase 3
  - [x] `src/App.tsx` — BrowserRouter con ruta `/` placeholder
  - [x] `src/pages/Home.tsx` — health check de API e IndexedDB
- [x] **Bloque 2.2 — Layout y navegación**
  - [x] `src/components/layout/AppLayout.tsx` — layout wrapper con `<Outlet />`
  - [x] `src/components/layout/BottomNav.tsx` — bottom nav mobile (hidden md+), SVGs inline
  - [x] `src/components/layout/Sidebar.tsx` — sidebar desktop (hidden mobile, visible md+)
  - [x] 5 rutas: `/`, `/comprobantes`, `/ingresos`, `/contactos`, `/reportes`
  - [x] Páginas placeholder: Comprobantes, Ingresos, Contactos, Reportes
  - [x] Activo via `useLocation()` / `NavLink`, sin Zustand
- [ ] **Bloque 2.3 — Pantallas CRUD (Comprobantes, Contactos, Ingresos)**
- [ ] **Bloque 2.4 — Flujo offline**
- [ ] **Bloque 2.5 — Reportes con Recharts**

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

**Bloque 2.2 completo.** Siguiente: **Bloque 2.3 — Pantallas CRUD (Comprobantes, Contactos, Ingresos)**

Antes de continuar, validar manualmente el bloque 2.2:
1. `cd frontend && npm run dev` → `http://localhost:5173`
2. Mobile (DevTools < 768px): bottom nav con 5 tabs, tab activo en azul
3. Desktop (> 768px): sidebar visible, bottom nav oculto
4. Navegar entre las 5 rutas: URL cambia, item activo se resalta
5. Home mantiene los status badges de API e IndexedDB

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
