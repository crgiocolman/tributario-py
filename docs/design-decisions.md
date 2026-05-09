# docs/design-decisions.md — Historial de decisiones de diseño

Razonamiento detrás de las decisiones que hoy son reglas en `CLAUDE.md`. Referencia para entender el **por qué**, no para escribir código.

---

## BIGINT para montos, no DECIMAL

**Decisión:** Todos los montos en BIGINT (guaraníes enteros).

**Por qué:** PYG no tiene decimales. DECIMAL introduce errores de redondeo innecesarios y complejidad en comparaciones. BIGINT es exacto, performante, y consistente con cómo Marangatu maneja los montos internamente.

---

## UUID v4 generado en el cliente

**Decisión:** PKs son UUID v4 generados en el dispositivo que crea el registro.

**Por qué:** La app es offline-first. Si el celular crea un comprobante sin conexión, necesita un PK inmediato para vincular la imputación fiscal y los adjuntos. Con autoincrement, tendría que esperar al sync para obtener el ID real, lo que complica toda la lógica de relaciones offline.

**Trade-off aceptado:** UUIDs son más pesados que integers (16 bytes vs 4). Para ~40 registros/mes es irrelevante.

---

## ImputaciónFiscal como tabla separada (1:1 con Comprobante)

**Decisión:** La imputación no son columnas dentro de Comprobante, sino una tabla propia.

**Por qué:** Las imputaciones se rectifican independientemente del comprobante (RG 90/2021 Art. 9 permite rectificar sin multa adicional). Necesitamos trackear cuándo se rectificó, por qué, y cuál era el valor anterior. Meter eso en la tabla Comprobante ensuciaría una entidad que debería ser inmutable (el documento fiscal no cambia, solo su tratamiento tributario).

---

## Ingreso como tabla separada de Comprobante

**Decisión:** Tabla `ingresos` separada, con FK opcional a `comprobantes`.

**Por qué:** Un salario tiene campos que no existen en una factura (aporte IPS, aguinaldo exonerado, período devengado vs. percibido, acumulado anual para tracking del umbral 80M). No todos los ingresos tienen comprobante asociado (el salario tiene liquidación de sueldo, no factura). Forzar todo en `comprobantes` requeriría campos nullable que solo aplican a un tipo.

---

## Last-write-wins para sync

**Decisión:** Conflictos de sincronización se resuelven por `updated_at` más reciente.

**Por qué:** Un solo usuario con dos dispositivos. Los conflictos reales son raros (tendrías que editar el mismo comprobante desde celular y PC entre syncs). Estrategias más sofisticadas (CRDT, merge manual) agregan complejidad desproporcionada para el volumen y uso.

---

## Comprobante + Imputación en una sola request

**Decisión:** POST `/comprobantes` crea comprobante e imputación atómicamente.

**Por qué:** El flujo del usuario es: foto → montos → categoría → guardar. No tiene sentido crear un comprobante "sin imputación" y después agregar la imputación como paso separado. Una sola transacción garantiza consistencia y simplifica el frontend.

---

## ConfiguraciónFiscal con tasas por año

**Decisión:** Una fila por año fiscal con todas las tasas y umbrales.

**Por qué:** Si la ley cambia en 2027 (nuevo tramo, nuevo umbral), se crea una nueva fila sin afectar los cálculos históricos. Hardcodear tasas en el código haría imposible recalcular años anteriores correctamente.

---

## PWA en lugar de React Native/Flutter

**Decisión:** Progressive Web App con React + Vite.

**Por qué:** El requisito es celular + PC con offline. Una PWA cubre ambos sin aprender un framework móvil nuevo. Service Worker + IndexedDB dan offline real. Se instala desde el browser como app. El usuario ya conoce React (frontend web estándar). Para un proyecto personal sin publicación en stores, es la opción de menor fricción.

---

## SQLAlchemy async con asyncpg

**Decisión:** Usar el modo async de SQLAlchemy 2.0.

**Por qué:** FastAPI es async-native. Mezclar sync SQLAlchemy con async FastAPI funciona pero requiere `run_in_executor` implícito y pierde las ventajas de concurrencia. El proyecto existente (SiuChat) usa sync, pero este proyecto arranca de cero y el owner está cómodo con async.

---

## Archivos adjuntos en disco local, no en BD

**Decisión:** PDFs y fotos se guardan en `{STORAGE_PATH}/{año}/{mes}/{uuid}.{ext}`. La BD solo guarda la referencia.

**Por qué:** Guardar blobs en PostgreSQL infla la BD, complica backups, y no escala. Disco local es simple, rápido, y suficiente para uso personal. Si algún día se migra a S3 o similar, solo cambia `storage_service.py`.

---

## Cómo agregar nuevas decisiones

Cuando se tome una decisión que merezca ir a `CLAUDE.md` como regla, agregarla también acá con su razonamiento:

```
### [Nombre corto de la decisión]

**Decisión:** [Qué se decidió, una oración]

**Por qué:** [Contexto, alternativas consideradas, justificación]
```
