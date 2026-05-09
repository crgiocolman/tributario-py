import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import (
    CargadoMarangatu,
    Condicion,
    FormaEmision,
    FormaPago,
    SyncStatus,
    TipoComprobante,
    TipoOperacion,
)

_vc = lambda obj: [e.value for e in obj]  # noqa: E731


class Comprobante(Base):
    __tablename__ = "comprobantes"

    id = sa.Column(UUID(as_uuid=True), primary_key=True)
    contacto_id = sa.Column(
        UUID(as_uuid=True),
        sa.ForeignKey("contactos.id", name="fk_comprobantes_contacto_id", ondelete="RESTRICT"),
        nullable=False,
    )
    tipo_operacion = sa.Column(
        sa.Enum(TipoOperacion, values_callable=_vc, name="tipo_operacion"),
        nullable=False,
    )
    tipo_comprobante = sa.Column(
        sa.Enum(TipoComprobante, values_callable=_vc, name="tipo_comprobante"),
        nullable=False,
    )
    forma_emision = sa.Column(
        sa.Enum(FormaEmision, values_callable=_vc, name="forma_emision"),
        nullable=False,
    )
    numero_timbrado = sa.Column(sa.String(20), nullable=True)
    numero_comprobante = sa.Column(sa.String(25), nullable=True)
    fecha_emision = sa.Column(sa.Date, nullable=False)
    fecha_percepcion = sa.Column(sa.Date, nullable=True)
    condicion = sa.Column(
        sa.Enum(Condicion, values_callable=_vc, name="condicion"),
        nullable=False,
    )
    moneda = sa.Column(sa.String(3), nullable=False)
    tipo_cambio = sa.Column(sa.Numeric(12, 4), nullable=True)
    monto_exento = sa.Column(sa.BigInteger, nullable=False)
    monto_gravado_5 = sa.Column(sa.BigInteger, nullable=False)
    iva_5 = sa.Column(sa.BigInteger, nullable=False)
    monto_gravado_10 = sa.Column(sa.BigInteger, nullable=False)
    iva_10 = sa.Column(sa.BigInteger, nullable=False)
    total = sa.Column(sa.BigInteger, nullable=False)
    forma_pago = sa.Column(
        sa.Enum(FormaPago, values_callable=_vc, name="forma_pago"),
        nullable=True,
    )
    concepto = sa.Column(sa.Text, nullable=True)
    periodo_fiscal = sa.Column(sa.String(7), nullable=False)
    cargado_marangatu = sa.Column(
        sa.Enum(CargadoMarangatu, values_callable=_vc, name="cargado_marangatu"),
        nullable=False,
    )
    notas = sa.Column(sa.Text, nullable=True)
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False)
    updated_at = sa.Column(sa.DateTime(timezone=True), nullable=False)
    deleted_at = sa.Column(sa.DateTime(timezone=True), nullable=True)
    sync_status = sa.Column(
        sa.Enum(SyncStatus, values_callable=_vc, name="sync_status"),
        nullable=False,
    )
    device_id = sa.Column(sa.String(50), nullable=True)

    __table_args__ = (
        sa.UniqueConstraint("numero_timbrado", "numero_comprobante", name="uq_comprobantes_timbrado_numero"),
        sa.Index("ix_comprobantes_contacto_id", "contacto_id"),
        sa.Index("ix_comprobantes_periodo_fiscal", "periodo_fiscal"),
        sa.Index("ix_comprobantes_tipo_operacion", "tipo_operacion"),
        sa.Index("ix_comprobantes_fecha_emision", "fecha_emision"),
    )

    contacto = relationship("Contacto", back_populates="comprobantes")
    archivos_adjuntos = relationship("ArchivoAdjunto", back_populates="comprobante")
    imputacion_fiscal = relationship("ImputacionFiscal", back_populates="comprobante", uselist=False)
    ingresos = relationship("Ingreso", back_populates="comprobante")
