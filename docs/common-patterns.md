# docs/common-patterns.md — Patrones de código del proyecto

Patrones recurrentes en TributarioPY. Referencia para Claude Code cuando replica un patrón existente.

Este archivo se irá llenando a medida que el proyecto avance. Los patrones iniciales vienen del diseño, no de código real aún.

---

## Enums Python + PostgreSQL nativos

```python
# app/enums.py
from enum import Enum

class TipoOperacion(str, Enum):
    COMPRA = "compra"
    VENTA = "venta"

class TipoComprobante(str, Enum):
    FACTURA = "factura"
    AUTOFACTURA = "autofactura"
    TICKET = "ticket"
    NOTA_CREDITO = "nota_credito"
    NOTA_DEBITO = "nota_debito"
    BOLETA_RESIMPLE = "boleta_resimple"
    LIQUIDACION_SALARIO = "liquidacion_salario"
```

En el modelo SQLAlchemy:

```python
from sqlalchemy import Enum as SQLEnum

tipo_operacion = Column(
    SQLEnum(
        TipoOperacion,
        name="tipo_operacion",
        native_enum=True,
        create_type=True,
        values_callable=lambda obj: [e.value for e in obj],
    ),
    nullable=False,
)
```

---

## FK con nombre explícito

```python
contacto_id = Column(
    UUID(as_uuid=True),
    ForeignKey("contactos.id", ondelete="RESTRICT", name="fk_comprobantes_contacto_id"),
    nullable=False,
)
```

Convenciones:
- FK: `fk_<tabla>_<columna>`
- Unique: `uq_<tabla>_<columna>` o `uq_<tabla>_<col1>_<col2>`
- Índice: `ix_<tabla>_<columna>`

---

## Timestamp con timezone

```python
from datetime import datetime, timezone

now = datetime.now(timezone.utc)  # Correcto
# datetime.utcnow()  # MAL — deprecated
```

SQLAlchemy:
```python
created_at = Column(
    DateTime(timezone=True),
    nullable=False,
    server_default=func.now(),
)
```

---

## Montos en BIGINT

```python
# Siempre guaraníes enteros
monto_gravado_10 = Column(BigInteger, nullable=False, default=0)
iva_10 = Column(BigInteger, nullable=False, default=0)
total = Column(BigInteger, nullable=False, default=0)
```

Nunca `Numeric`, `Float`, ni `Decimal` para montos en PYG.

---

## Creación atómica comprobante + imputación

```python
async def crear_comprobante_con_imputacion(
    db: AsyncSession,
    comprobante_data: ComprobanteCreate,
) -> Comprobante:
    comprobante = Comprobante(**comprobante_data.model_dump(exclude={"imputacion"}))
    db.add(comprobante)

    imputacion = ImputacionFiscal(
        comprobante_id=comprobante.id,
        **comprobante_data.imputacion.model_dump(),
    )
    db.add(imputacion)

    await db.flush()
    # Recalcular período fiscal
    await recalcular_periodo(db, comprobante.periodo_fiscal)
    await db.commit()
    return comprobante
```

Una transacción, un commit. Si falla cualquier parte, rollback completo.

---

## Mixins para campos comunes

```python
# app/models/mixins.py
from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func

class TimestampMixin:
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

class SoftDeleteMixin:
    deleted_at = Column(DateTime(timezone=True), nullable=True)

class SyncMixin:
    sync_status = Column(String(10), nullable=False, default="pending")
    device_id = Column(String(50), nullable=True)
```

---

## Settings con pydantic-settings

```python
# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    STORAGE_PATH: str = "./storage"

settings = Settings()
```
