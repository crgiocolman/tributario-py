# ERD — App Tributaria Personal Paraguay

## Convenciones

- **PK**: Primary Key (UUID v4, generado en cliente para soporte offline)
- **FK**: Foreign Key
- **Timestamps**: `created_at`, `updated_at` en todas las tablas (UTC)
- **Soft delete**: `deleted_at` nullable en tablas principales
- **Sync**: `sync_status` (pending/synced/conflict) + `device_id` en tablas editables desde el móvil

---

## 1. Contacto

Clientes y proveedores. Un contacto puede ser ambos.

| Campo | Tipo | Nullable | Descripción |
|---|---|---|---|
| `id` | UUID | PK | |
| `ruc` | VARCHAR(15) | NOT NULL | RUC con dígito verificador. Ej: "80012345-6" |
| `razon_social` | VARCHAR(200) | NOT NULL | Razón social legal |
| `nombre_fantasia` | VARCHAR(200) | YES | Nombre comercial. Ej: "Los Mil Colores" |
| `tipo` | ENUM | NOT NULL | `cliente`, `proveedor`, `ambos` |
| `tipo_contribuyente` | ENUM | YES | `persona_fisica`, `persona_juridica` |
| `telefono` | VARCHAR(20) | YES | |
| `email` | VARCHAR(100) | YES | |
| `direccion` | TEXT | YES | |
| `notas` | TEXT | YES | Observaciones libres |
| `es_frecuente` | BOOLEAN | NOT NULL | Default false. Para sugerencias rápidas |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |
| `deleted_at` | TIMESTAMPTZ | YES | Soft delete |
| `sync_status` | VARCHAR(10) | NOT NULL | `pending`, `synced`, `conflict` |
| `device_id` | VARCHAR(50) | YES | Dispositivo que creó/editó |

**Índices**: `ruc` (UNIQUE), `tipo`

---

## 2. CategoriaIRP

Catálogo de categorías deducibles para el IRP-RSP. Basado en Ley 6380/2019 Art. 64.

| Campo | Tipo | Nullable | Descripción |
|---|---|---|---|
| `id` | UUID | PK | |
| `codigo` | VARCHAR(30) | NOT NULL | Código interno. Ej: "ALIMENTACION" |
| `nombre` | VARCHAR(100) | NOT NULL | Nombre para UI. Ej: "Alimentación" |
| `descripcion` | TEXT | YES | Detalle y ejemplos |
| `articulo_ley` | VARCHAR(50) | YES | Referencia legal. Ej: "Art. 64 num. 1" |
| `limite_porcentaje` | DECIMAL(5,2) | YES | Si tiene tope (ej: 1% sobre ingresos brutos) |
| `activo` | BOOLEAN | NOT NULL | Default true |
| `orden` | INTEGER | NOT NULL | Orden de aparición en UI |

**Seed data** (precargado):
- `ALIMENTACION` — Alimentación
- `VESTIMENTA` — Vestimenta
- `ALQUILER_VIVIENDA` — Alquiler vivienda
- `MANTENIMIENTO_VIVIENDA` — Mantenimiento vivienda
- `MOBILIARIO_HOGAR` — Mobiliario / electrodomésticos / enseres hogar
- `ESPARCIMIENTO` — Esparcimiento (cine, gimnasio, barbería, mascotas)
- `SALUD` — Salud (consultas, medicamentos, seguros médicos)
- `EDUCACION` — Educación (cursos, libros, capacitaciones)
- `VEHICULO` — Vehículo (combustible, mantenimiento, compra cada 3 años)
- `SERVICIOS_BASICOS` — Servicios básicos (luz, agua, internet, teléfono)
- `APORTE_IPS` — Aporte IPS trabajador
- `DONACIONES` — Donaciones
- `ACTIVIDAD_GRAVADA` — Gastos vinculados a actividad profesional
- `SERVICIOS_FINANCIEROS` — Intereses de préstamos, seguros
- `NO_DEDUCIBLE` — No deducible (no cuenta para IRP)
- `NO_IMPUTAR` — No imputar a ningún impuesto

---

## 3. ReglaImputacion

Mapeo automático: cuando el usuario elige una categoría, la app sugiere la imputación fiscal correcta.

| Campo | Tipo | Nullable | Descripción |
|---|---|---|---|
| `id` | UUID | PK | |
| `categoria_irp_id` | UUID | FK → CategoriaIRP | |
| `imputa_iva_credito` | BOOLEAN | NOT NULL | ¿Se usa como crédito fiscal IVA? |
| `imputa_iva_credito_porcentaje` | DECIMAL(5,2) | YES | Si es parcial. Ej: 50 para internet mixto |
| `imputa_irp` | BOOLEAN | NOT NULL | ¿Se imputa al IRP-RSP? |
| `destino_reg_comprobante` | VARCHAR(20) | NOT NULL | `IVA`, `IRP-RSP`, `NO_IMPUTAR` |
| `notas` | TEXT | YES | Justificación o referencia normativa |

**Seed data** (basado en decisiones ya tomadas):

| Categoría | IVA Créd. | % | IRP | Destino Reg. |
|---|---|---|---|---|
| ACTIVIDAD_GRAVADA | true | 100 | true | IRP-RSP |
| SERVICIOS_BASICOS | true | 50 | true | IRP-RSP |
| ALIMENTACION | false | — | true | IRP-RSP |
| VESTIMENTA | false | — | true | IRP-RSP |
| ALQUILER_VIVIENDA | false | — | true | IRP-RSP |
| VEHICULO | false | — | true | IRP-RSP |
| SALUD | false | — | true | IRP-RSP |
| ESPARCIMIENTO | false | — | true | IRP-RSP |
| EDUCACION | false | — | true | IRP-RSP |
| SERVICIOS_FINANCIEROS | false | — | true | IRP-RSP |
| DONACIONES | false | — | true | IRP-RSP |
| MANTENIMIENTO_VIVIENDA | false | — | true | IRP-RSP |
| MOBILIARIO_HOGAR | false | — | true | IRP-RSP |
| APORTE_IPS | false | — | true | IRP-RSP |
| NO_DEDUCIBLE | false | — | false | NO_IMPUTAR |
| NO_IMPUTAR | false | — | false | NO_IMPUTAR |

---

## 4. Comprobante

El documento fiscal en sí. Un comprobante puede tener múltiples líneas de transacción.

| Campo | Tipo | Nullable | Descripción |
|---|---|---|---|
| `id` | UUID | PK | |
| `contacto_id` | UUID | FK → Contacto | Emisor (compras) o receptor (ventas) |
| `tipo_operacion` | ENUM | NOT NULL | `compra`, `venta` |
| `tipo_comprobante` | ENUM | NOT NULL | `factura`, `autofactura`, `ticket`, `nota_credito`, `nota_debito`, `boleta_resimple`, `liquidacion_salario` |
| `forma_emision` | ENUM | NOT NULL | `electronica`, `virtual`, `preimpresa`, `autoimpresor`, `no_aplica` |
| `numero_timbrado` | VARCHAR(20) | YES | Nulo para liquidaciones de sueldo |
| `numero_comprobante` | VARCHAR(25) | YES | Formato: 001-001-0000123 |
| `fecha_emision` | DATE | NOT NULL | Fecha del documento |
| `fecha_percepcion` | DATE | YES | Fecha de cobro/pago efectivo (criterio percibido IRP) |
| `condicion` | ENUM | NOT NULL | `contado`, `credito` |
| `moneda` | VARCHAR(3) | NOT NULL | Default "PYG". Futuro: USD, BRL |
| `tipo_cambio` | DECIMAL(12,4) | YES | Si moneda != PYG |
| `monto_exento` | BIGINT | NOT NULL | En guaraníes (sin decimales) |
| `monto_gravado_5` | BIGINT | NOT NULL | Base imponible al 5% |
| `iva_5` | BIGINT | NOT NULL | Crédito/débito fiscal al 5% |
| `monto_gravado_10` | BIGINT | NOT NULL | Base imponible al 10% |
| `iva_10` | BIGINT | NOT NULL | Crédito/débito fiscal al 10% |
| `total` | BIGINT | NOT NULL | Suma de todo |
| `forma_pago` | ENUM | YES | `efectivo`, `transferencia`, `tarjeta_credito`, `tarjeta_debito`, `cheque`, `mixto` |
| `concepto` | TEXT | YES | Descripción libre del comprobante |
| `periodo_fiscal` | VARCHAR(7) | NOT NULL | "YYYY-MM" al que corresponde. Ej: "2026-04" |
| `cargado_marangatu` | ENUM | NOT NULL | `si`, `no`, `auto` (electrónicos se autocargan) |
| `notas` | TEXT | YES | |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |
| `deleted_at` | TIMESTAMPTZ | YES | |
| `sync_status` | VARCHAR(10) | NOT NULL | |
| `device_id` | VARCHAR(50) | YES | |

**Índices**: `contacto_id`, `periodo_fiscal`, `tipo_operacion`, `fecha_emision`, (`numero_timbrado`, `numero_comprobante`) UNIQUE (nullable)

**Nota sobre montos**: Se usan BIGINT en guaraníes porque PYG no tiene decimales. Esto evita errores de redondeo con DECIMAL y es consistente con cómo Marangatu maneja los montos.

---

## 5. ArchivoAdjunto

Fotos y PDFs vinculados a comprobantes. Soporta múltiples archivos por comprobante.

| Campo | Tipo | Nullable | Descripción |
|---|---|---|---|
| `id` | UUID | PK | |
| `comprobante_id` | UUID | FK → Comprobante | |
| `nombre_archivo` | VARCHAR(255) | NOT NULL | Nombre original del archivo |
| `tipo_mime` | VARCHAR(50) | NOT NULL | Ej: "image/jpeg", "application/pdf" |
| `tamano_bytes` | BIGINT | NOT NULL | |
| `ruta_almacenamiento` | TEXT | NOT NULL | Ruta en el server local |
| `hash_sha256` | VARCHAR(64) | YES | Para detectar duplicados y verificar integridad |
| `sync_status` | VARCHAR(10) | NOT NULL | |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

**Nota offline**: En IndexedDB se guarda el blob del archivo. Al sincronizar, se envía al backend y se reemplaza por la referencia a la ruta del server.

---

## 6. ImputacionFiscal

Cómo se imputa cada comprobante a efectos de IVA e IRP. Relación 1:1 con Comprobante (un comprobante tiene una imputación).

| Campo | Tipo | Nullable | Descripción |
|---|---|---|---|
| `id` | UUID | PK | |
| `comprobante_id` | UUID | FK → Comprobante | UNIQUE |
| `categoria_irp_id` | UUID | FK → CategoriaIRP | |
| `imputa_iva_credito` | BOOLEAN | NOT NULL | |
| `iva_credito_porcentaje` | DECIMAL(5,2) | NOT NULL | Default 100. Para internet: 50 |
| `iva_credito_monto` | BIGINT | NOT NULL | Monto efectivo de IVA crédito utilizado |
| `imputa_irp` | BOOLEAN | NOT NULL | |
| `destino_reg_comprobante` | VARCHAR(20) | NOT NULL | `IVA`, `IRP-RSP`, `NO_IMPUTAR` |
| `a_nombre_de` | VARCHAR(100) | YES | "yo" o nombre familiar a cargo |
| `rectificado` | BOOLEAN | NOT NULL | Default false. True si se cambió post-presentación |
| `fecha_rectificacion` | TIMESTAMPTZ | YES | |
| `notas_rectificacion` | TEXT | YES | Motivo del cambio |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |

---

## 7. Ingreso

Registro específico de ingresos salariales y otros ingresos no facturados. Complementa a Comprobante para capturar datos exclusivos de relación de dependencia.

| Campo | Tipo | Nullable | Descripción |
|---|---|---|---|
| `id` | UUID | PK | |
| `comprobante_id` | UUID | FK → Comprobante | YES. Nullable si no hay factura (ej: salario) |
| `contacto_id` | UUID | FK → Contacto | El empleador o pagador |
| `tipo_ingreso` | ENUM | NOT NULL | `salario`, `aguinaldo`, `vacaciones`, `liquidacion_final`, `honorarios`, `otros` |
| `periodo_devengado` | VARCHAR(7) | NOT NULL | Mes al que corresponde el trabajo. Ej: "2025-10" |
| `fecha_percepcion` | DATE | NOT NULL | Fecha efectiva de cobro (criterio IRP) |
| `monto_bruto` | BIGINT | NOT NULL | |
| `aporte_ips_trabajador` | BIGINT | NOT NULL | Default 0. Típicamente 9% del bruto |
| `otros_descuentos` | BIGINT | NOT NULL | Default 0. Anticipos, préstamos internos |
| `monto_exonerado` | BIGINT | NOT NULL | Default 0. Aguinaldo, indemnización legal |
| `monto_computable_irp` | BIGINT | NOT NULL | bruto - IPS - exonerado |
| `es_gravado_irp` | BOOLEAN | NOT NULL | False para aguinaldo |
| `acumulado_anual` | BIGINT | YES | Calculado. Tracking del umbral 80M |
| `notas` | TEXT | YES | Ej: "Liquidación final EBSA, incluye vacaciones" |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |
| `sync_status` | VARCHAR(10) | NOT NULL | |
| `device_id` | VARCHAR(50) | YES | |

**Nota**: `acumulado_anual` se calcula al guardar sumando todos los `monto_computable_irp` del año fiscal hasta esa fecha de percepción. Sirve para alertar cuando se cruza el umbral de 80M.

---

## 8. PeriodoFiscal

Resumen precalculado por mes. Se regenera al modificar comprobantes del período.

| Campo | Tipo | Nullable | Descripción |
|---|---|---|---|
| `id` | UUID | PK | |
| `periodo` | VARCHAR(7) | NOT NULL | "YYYY-MM". Ej: "2026-04" |
| `anio_fiscal` | INTEGER | NOT NULL | Año del ejercicio fiscal |
| `total_ventas_gravadas_10` | BIGINT | NOT NULL | |
| `total_ventas_gravadas_5` | BIGINT | NOT NULL | |
| `total_ventas_exentas` | BIGINT | NOT NULL | |
| `total_iva_debito` | BIGINT | NOT NULL | |
| `total_compras_gravadas_10` | BIGINT | NOT NULL | |
| `total_compras_gravadas_5` | BIGINT | NOT NULL | |
| `total_compras_exentas` | BIGINT | NOT NULL | |
| `total_iva_credito_utilizado` | BIGINT | NOT NULL | Solo el efectivamente imputado |
| `saldo_iva` | BIGINT | NOT NULL | Débito - Crédito (positivo = a pagar) |
| `total_ingresos_irp` | BIGINT | NOT NULL | Salarios + honorarios computables |
| `total_egresos_irp` | BIGINT | NOT NULL | Egresos imputados al IRP |
| `cantidad_comprobantes_compras` | INTEGER | NOT NULL | |
| `cantidad_comprobantes_ventas` | INTEGER | NOT NULL | |
| `f120_presentado` | BOOLEAN | NOT NULL | Default false |
| `f120_fecha_presentacion` | TIMESTAMPTZ | YES | |
| `reg_comprobantes_presentado` | BOOLEAN | NOT NULL | Default false |
| `reg_comprobantes_fecha` | TIMESTAMPTZ | YES | |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |

**Índices**: `periodo` (UNIQUE), `anio_fiscal`

---

## 9. DeclaracionJurada

Registro de DJ presentadas ante la DNIT.

| Campo | Tipo | Nullable | Descripción |
|---|---|---|---|
| `id` | UUID | PK | |
| `periodo_fiscal_id` | UUID | FK → PeriodoFiscal | YES. Null para F515 que cubre un año |
| `formulario` | ENUM | NOT NULL | `F120`, `F515`, `REG_COMPROBANTES` |
| `periodo` | VARCHAR(7) | NOT NULL | "YYYY-MM" o "YYYY" para anuales |
| `numero_orden` | VARCHAR(20) | YES | Número que asigna Marangatu |
| `fecha_presentacion` | TIMESTAMPTZ | NOT NULL | |
| `es_rectificativa` | BOOLEAN | NOT NULL | Default false |
| `rectifica_a` | UUID | FK → DeclaracionJurada | YES. DJ original que rectifica |
| `monto_impuesto` | BIGINT | NOT NULL | Default 0 |
| `monto_multa` | BIGINT | NOT NULL | Default 0 |
| `monto_intereses` | BIGINT | NOT NULL | Default 0 |
| `monto_mora` | BIGINT | NOT NULL | Default 0 |
| `monto_total_pagado` | BIGINT | NOT NULL | |
| `fecha_pago` | TIMESTAMPTZ | YES | |
| `estado` | ENUM | NOT NULL | `presentada`, `pagada`, `pendiente`, `vencida` |
| `notas` | TEXT | YES | |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |

---

## 10. ConfiguracionFiscal

Parámetros del contribuyente y constantes fiscales. Una sola fila activa por año fiscal.

| Campo | Tipo | Nullable | Descripción |
|---|---|---|---|
| `id` | UUID | PK | |
| `anio_fiscal` | INTEGER | NOT NULL | |
| `ruc` | VARCHAR(15) | NOT NULL | |
| `razon_social` | VARCHAR(200) | NOT NULL | |
| `ultimo_digito_ruc` | INTEGER | NOT NULL | Para calcular vencimientos |
| `umbral_irp` | BIGINT | NOT NULL | 80.000.000 (puede cambiar por ley) |
| `tramo_irp_1_hasta` | BIGINT | NOT NULL | 50.000.000 |
| `tramo_irp_1_tasa` | DECIMAL(4,2) | NOT NULL | 8.00 |
| `tramo_irp_2_hasta` | BIGINT | NOT NULL | 150.000.000 |
| `tramo_irp_2_tasa` | DECIMAL(4,2) | NOT NULL | 9.00 |
| `tramo_irp_3_tasa` | DECIMAL(4,2) | NOT NULL | 10.00 |
| `tasa_iva_general` | DECIMAL(4,2) | NOT NULL | 10.00 |
| `tasa_iva_reducida` | DECIMAL(4,2) | NOT NULL | 5.00 |
| `multa_dj_determinativa` | BIGINT | NOT NULL | 50.000 |
| `multa_dj_informativa` | BIGINT | NOT NULL | 100.000 |
| `tasa_interes_diario` | DECIMAL(6,4) | NOT NULL | 0.0500 (0.05%/día) |
| `fecha_inicio_ejercicio` | DATE | NOT NULL | Normalmente 01/01. Ejercicio corto: 14/11/2025 |
| `fecha_fin_ejercicio` | DATE | NOT NULL | Normalmente 31/12 |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |

**Índices**: `anio_fiscal` (UNIQUE)

---

## Relaciones (resumen)

```
Contacto 1──N Comprobante         (un contacto tiene muchos comprobantes)
Comprobante 1──1 ImputacionFiscal  (cada comprobante tiene una imputación)
Comprobante 1──N ArchivoAdjunto    (un comprobante puede tener varios adjuntos)
CategoriaIRP 1──1 ReglaImputacion  (cada categoría tiene su regla default)
CategoriaIRP 1──N ImputacionFiscal (cada imputación referencia una categoría)
Contacto 1──N Ingreso             (un empleador/pagador tiene muchos ingresos)
Ingreso N──1 Comprobante          (un ingreso puede estar vinculado a un comprobante, opcional)
PeriodoFiscal 1──N DeclaracionJurada (un período puede tener varias DJ: original + rectificativas)
DeclaracionJurada N──1 DeclaracionJurada (rectificativa → original)
```
