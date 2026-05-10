# docs/roadmap.md — Roadmap de TributarioPY

---

## Fase 1 — Backend core

**Objetivo:** API REST funcional con todas las entidades, seed data, y endpoints CRUD + reportes + exportación.

**Bloques:**
- **1.1** Setup inicial (estructura, Docker, FastAPI, Alembic)
- **1.2** Modelos SQLAlchemy + migración (10 tablas, enums nativos)
- **1.3** Seed data (categorías IRP, reglas imputación, config fiscal 2025-2026)
- **1.4** API CRUD (contactos, comprobantes, ingresos, adjuntos, períodos, DJ, imputaciones)
- **1.5** Reportes y exportación (dashboard, IVA mensual, proyección IRP, CSV Reg. Comprob., resumen F120/F515)

---

## Fase 2 — Frontend PWA

**Objetivo:** Interfaz móvil usable offline. Flujo principal: foto → montos → categoría → guardado.

**Bloques:**
- **2.1** Setup React + Vite + Tailwind + PWA manifest + Service Worker básico + IndexedDB con Dexie.js (esquema local espejo de PostgreSQL) ✓
- **2.2** Layout y navegación (shell, sidebar/bottom nav, rutas principales)
- **2.3** Pantallas CRUD: lista de comprobantes, formulario de carga rápida, lista de contactos, ingresos
- **2.4** Flujo offline: cámara/galería → captura → formulario con sugerencia de imputación automática
- **2.5** Dashboard con gráficos (Recharts): IVA mensual, egresos por categoría, proyección IRP

---

## Fase 3 — Sincronización

**Objetivo:** Los datos del celular se sincronizan con el backend en la PC de casa.

**Bloques:**
- **3.1** Sync engine en frontend (cola de cambios, push/pull, backoff)
- **3.2** Endpoints de sync en backend (push, pull, status)
- **3.3** Sync de archivos adjuntos (multipart, separado de datos)
- **3.4** UI de estado de sync (indicador, errores, retry manual)

---

## Fase 4 — Exportación y validación

**Objetivo:** Generar archivos listos para Marangatu y validar datos antes de presentar.

**Bloques:**
- **4.1** Exportación CSV Reg. Comprobantes (verificar formato contra plantilla actual de Marangatu)
- **4.2** Resumen pre-armado F120 (JSON/PDF con totales para llenar manualmente)
- **4.3** Resumen pre-armado F515 (consolidación anual por categoría IRP)
- **4.4** Validaciones pre-presentación: comprobantes sin categoría, períodos sin comprobantes, montos inconsistentes
- **4.5** Backup ZIP de comprobantes por año

---

## Fase 5 — Mejoras UX (opcional, post-MVP)

**Bloques posibles:**
- OCR básico sobre foto de factura (extraer RUC, monto, fecha automáticamente)
- Contactos frecuentes con categoría sugerida automática
- Notificaciones de vencimiento (push o local)
- Modo oscuro
- Multi-año (navegación entre ejercicios fiscales)
