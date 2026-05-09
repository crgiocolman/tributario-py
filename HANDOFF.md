# HANDOFF.md — Estado actual operativo

Memoria operativa del proyecto. Leer esto primero al retomar después de una pausa.

**Última actualización:** Proyecto en fase de diseño. Cero código escrito.

---

## Fase actual

**Fase 1 — Backend core (modelos + API + seed)**

Progreso:

- [ ] **Bloque 1.1 — Setup inicial**
  - [ ] Crear estructura de carpetas
  - [ ] Docker Compose para PostgreSQL
  - [ ] Configuración FastAPI + SQLAlchemy async + Alembic
  - [ ] `.env` con variables base
- [ ] **Bloque 1.2 — Modelos y migración**
  - [ ] Modelos SQLAlchemy (10 tablas según ERD)
  - [ ] Enums PostgreSQL nativos
  - [ ] Migración inicial Alembic
  - [ ] Ciclo upgrade/downgrade/upgrade validado
- [ ] **Bloque 1.3 — Seed data**
  - [ ] Categorías IRP (16 categorías)
  - [ ] Reglas de imputación por categoría
  - [ ] Configuración fiscal 2025 y 2026
- [ ] **Bloque 1.4 — API CRUD**
  - [ ] Contactos (CRUD + búsqueda)
  - [ ] Comprobantes + Imputación (creación atómica)
  - [ ] Ingresos (CRUD + acumulado anual)
  - [ ] Adjuntos (upload multipart)
  - [ ] Períodos fiscales (listado + recálculo)
  - [ ] Declaraciones juradas (registro)
  - [ ] Imputaciones (rectificación individual + batch)
- [ ] **Bloque 1.5 — Reportes y exportación**
  - [ ] Dashboard resumen
  - [ ] IVA mensual
  - [ ] Proyección IRP
  - [ ] Exportación CSV Reg. Comprobantes
  - [ ] Exportación resumen F120 / F515

Detalle del roadmap en `docs/roadmap.md`.

---

## Estado BD local

- Alembic head: (pendiente — primera migración no creada aún)
- 10 tablas por crear: `contactos`, `categorias_irp`, `reglas_imputacion`, `comprobantes`, `archivos_adjuntos`, `imputaciones_fiscales`, `ingresos`, `periodos_fiscales`, `declaraciones_juradas`, `configuracion_fiscal`

---

## Variables de entorno (.env local)

```
DATABASE_URL=postgresql+asyncpg://admin:admin123@localhost:5432/tributario_py
STORAGE_PATH=./storage
```

---

## Arranque del entorno local

```bash
# 1. PostgreSQL en Docker
docker compose up -d

# 2. Verificar
docker ps

# 3. Venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o: venv\Scripts\activate  # Windows

# 4. Dependencias
pip install -r requirements.txt

# 5. Migración
alembic upgrade head

# 6. Seed
python -m app.seed.run

# 7. FastAPI
uvicorn app.main:app --reload
```

---

## Próximo paso concreto

**Bloque 1.1 — Setup inicial**

1. Crear estructura de carpetas según `docs/especificacion_tecnica.md` sección 4
2. `docker-compose.yml` con PostgreSQL 16
3. `app/main.py` con FastAPI + CORS
4. `app/database.py` con async engine + session factory
5. `app/config.py` con pydantic-settings
6. `alembic init` + configurar `env.py` para async
7. `.env` con DATABASE_URL + STORAGE_PATH
8. Validar que levanta: `uvicorn app.main:app --reload` → responde en `/docs`

---

## Documentación del proyecto

| Archivo | Para qué | Frecuencia de cambio |
|---|---|---|
| `CLAUDE.md` | Reglas activas del proyecto | Bajo |
| `HANDOFF.md` (este) | Estado operativo actual | Alto |
| `docs/roadmap.md` | Fases y bloques | Bajo |
| `docs/design-decisions.md` | Historial de por qué | Bajo |
| `docs/common-patterns.md` | Patrones de código | Bajo |
| `docs/erd.md` | Modelo de datos detallado | Bajo |
| `docs/especificacion_tecnica.md` | API, sync, exportación | Bajo |
| `docs/comandos.md` | Referencia de comandos | Bajo |

---

## Cómo retomar después de pausa

1. Leer este archivo (HANDOFF.md) primero
2. `git log --oneline -20` para ver últimos commits
3. Verificar entorno local: `docker ps`, venv activado, `alembic current`
4. Levantar backend: `uvicorn app.main:app --reload`
5. Abrir Claude Code en la raíz del proyecto
