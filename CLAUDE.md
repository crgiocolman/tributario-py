# CLAUDE.md — Reglas del proyecto TributarioPY

App personal de gestión tributaria para Paraguay. PWA offline-first + API REST. Uso individual (un contribuyente, múltiples dispositivos).

Para contexto extendido: ver `docs/design-decisions.md` (historial de por qué), `docs/common-patterns.md` (patrones de código), `docs/roadmap.md` (fases), `HANDOFF.md` (estado actual operativo).

---

## Stack

**Backend:** FastAPI + SQLAlchemy 2.0 (async, asyncpg) + PostgreSQL 16 + Pydantic v2 + Alembic.
**Frontend:** React 18 + Vite + Tailwind CSS + Dexie.js (IndexedDB) + Recharts + Workbox.
**Infra:** Docker (solo PostgreSQL) + uvicorn local. Sin deploy a servidor externo.

---

## Arquitectura

- `Base` vive en `app/database.py`, no en `app/models/`
- Lógica de negocio en `app/services/`, nunca en `app/api/` (routers)
- Routers: validan con Pydantic y delegan a services
- Schemas Pydantic obligatorios para todo endpoint con datos externos
- Seeds en `app/seed/` — datos iniciales de categorías IRP, reglas de imputación, configuración fiscal

---

## Schema

- UUID v4 como PK en todas las tablas — generado en el cliente (soporte offline)
- Enums como tipos nativos de PostgreSQL, no strings con CHECK
- Enums Python heredan de `(str, Enum)`, miembros UPPERCASE, valores lowercase. Usar `values_callable=lambda obj: [e.value for e in obj]` en la columna SQLAlchemy
- Timestamps con timezone siempre: `DateTime(timezone=True)` / `TIMESTAMPTZ`
- `datetime.now(timezone.utc)` en Python. Nunca `datetime.utcnow()` (deprecated)
- FKs con `ON DELETE RESTRICT` por default. Borrados lógicos via `deleted_at`, no físicos
- Todas las FKs y unique constraints llevan `name="..."` explícito
- Montos en `BIGINT` (guaraníes sin decimales). Nunca `DECIMAL` ni `FLOAT` para PYG
- Campos de sync: `sync_status` (`pending`/`synced`/`conflict`) + `device_id` en tablas editables desde el móvil

---

## Patrones obligatorios

- `logger` para errores en services, nunca `print`
- `print` solo debug temporal, eliminar antes de commit
- Toda función que modifique BD vive en service, no en router
- `db.rollback()` en except antes de retornar
- Comprobante + ImputaciónFiscal se crean en una sola transacción (nunca por separado)
- PeriodoFiscal se recalcula automáticamente al modificar comprobantes del período
- Categorías IRP y ReglaImputación son datos semilla — no se crean desde la API, solo se consultan

---

## Reglas de negocio tributario (codificadas en services)

- IVA: tasa general 10%, reducida 5%. IVA crédito solo se imputa si la regla de la categoría lo permite
- IRP-RSP: escala progresiva sobre renta neta total — 8% hasta 50M, 9% de 50M a 150M, 10% en adelante. El umbral de 80M es filtro de entrada, no mínimo no imponible
- Vencimientos se calculan desde `ConfiguracionFiscal.ultimo_digito_ruc` (dígito 0 → día 25 IVA, 26 Reg. Comprob.)
- Criterio de lo percibido para IRP: el ingreso se registra cuando se cobra, no cuando se factura
- Aguinaldo exonerado de IRP. Aporte IPS (9%) se deduce del bruto antes de computar

---

## Sincronización offline

- Estrategia: offline-first, last-write-wins por `updated_at`
- Cola de cambios en IndexedDB (`sync_queue`), push al recuperar conexión
- Archivos adjuntos se sincronizan por separado (multipart), después de sus comprobantes padre
- Pull periódico cada 5 minutos si hay conexión
- Máximo 5 reintentos con backoff exponencial por item en cola

---

## Alembic

- Nunca DROP TABLE para agregar columnas
- Flujo: `alembic revision --autogenerate` → revisar el archivo → probar upgrade/downgrade/upgrade local → aceptar
- Alembic autogenerate tiene bugs conocidos: no emite ENUM DROP en downgrade, no siempre respeta orden de FKs entre tablas nuevas. Revisar siempre
- ADD COLUMN NOT NULL sobre tabla con datos: migración en 3 pasos (add nullable → backfill → alter not null)
- Seed data se ejecuta después de la primera migración, no dentro de ella

---

## Flujo de trabajo

1. Decisiones de diseño en Claude.ai, ejecución en Claude Code
2. Prompts a Claude Code referencian "siguiendo CLAUDE.md" en lugar de repetir reglas
3. Si Claude Code detecta que una regla contradice al código actual, o encuentra un caso no cubierto: parar y pedir clarificación. No improvisar. CLAUDE.md es fuente de verdad
4. Al terminar una tarea: resumen de 2-3 oraciones de qué cambió. Sin desglosar archivo por archivo salvo pedido explícito
5. Output de Claude Code se revisa antes de aceptar/commitear

---

## Trabajando con Claude Code

**Plan Mode obligatorio** para tareas que tocan más de un archivo. Activar con `Shift + Tab`. Proponer plan escrito antes de editar.

**Ejecución directa permitida** solo para: fixes chicos (1 archivo, <50 líneas), renombrar variables, agregar logs/docstrings, ejecutar diseños ya validados en Claude.ai.

**Revisión de diffs — qué rechazar automáticamente:**

- Timestamps sin timezone o `datetime.utcnow()`
- `except Exception: pass` que silencia errores
- Nombres autogenerados de constraints/FKs
- Montos con DECIMAL o FLOAT en lugar de BIGINT
- Lógica de negocio en routers en vez de services
- Diff >150 líneas en un archivo — pedir partir en cambios más chicos
- UUID generado en el server cuando debería generarse en el cliente

**Cuándo volver a Claude.ai:**

- Claude Code pregunta entre alternativas que afectan arquitectura
- Error cuya causa sospechás que es problema de diseño más profundo
- Acumulando deuda técnica por apuro

**Cuándo ir directo a Claude Code (sin diseño previo):**

- Renombrar una variable, agregar un log, arreglar un typo
- Fix de un bug trivial en un solo archivo
- Agregar un docstring o formatear código

**Comandos útiles:** `/clear` limpia contexto, `/compact` resume sesión, `think hard` / `ultrathink` en prompt aumenta thinking budget.

---

## Eficiencia de tokens

- Eliminar filler conversacional ("Certainly", "I hope this helps")
- No resumir el request ni explicar qué se va a hacer
- Partial updates only: proveer solo funciones/bloques que cambiaron, no archivos enteros
- Usar `// ... existing code ...` para indicar secciones sin cambios
- No re-declarar información ya presente en los archivos del proyecto o el chat
- Si la tarea es compleja: plan en 1-2 bullets antes de escribir código

---

## Retomar después de pausa

1. Leer `HANDOFF.md` primero
2. `git log --oneline -20` para últimos commits
3. Verificar entorno: `docker ps`, venv activado, `alembic current`
4. Abrir Claude Code en la raíz del proyecto (lee CLAUDE.md automático)
