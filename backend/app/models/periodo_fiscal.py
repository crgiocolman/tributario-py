import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class PeriodoFiscal(Base):
    __tablename__ = "periodos_fiscales"

    id = sa.Column(UUID(as_uuid=True), primary_key=True)
    periodo = sa.Column(sa.String(7), nullable=False)
    anio_fiscal = sa.Column(sa.Integer, nullable=False)
    total_ventas_gravadas_10 = sa.Column(sa.BigInteger, nullable=False)
    total_ventas_gravadas_5 = sa.Column(sa.BigInteger, nullable=False)
    total_ventas_exentas = sa.Column(sa.BigInteger, nullable=False)
    total_iva_debito = sa.Column(sa.BigInteger, nullable=False)
    total_compras_gravadas_10 = sa.Column(sa.BigInteger, nullable=False)
    total_compras_gravadas_5 = sa.Column(sa.BigInteger, nullable=False)
    total_compras_exentas = sa.Column(sa.BigInteger, nullable=False)
    total_iva_credito_utilizado = sa.Column(sa.BigInteger, nullable=False)
    saldo_iva = sa.Column(sa.BigInteger, nullable=False)
    total_ingresos_irp = sa.Column(sa.BigInteger, nullable=False)
    total_egresos_irp = sa.Column(sa.BigInteger, nullable=False)
    cantidad_comprobantes_compras = sa.Column(sa.Integer, nullable=False)
    cantidad_comprobantes_ventas = sa.Column(sa.Integer, nullable=False)
    f120_presentado = sa.Column(sa.Boolean, nullable=False, default=False)
    f120_fecha_presentacion = sa.Column(sa.DateTime(timezone=True), nullable=True)
    reg_comprobantes_presentado = sa.Column(sa.Boolean, nullable=False, default=False)
    reg_comprobantes_fecha = sa.Column(sa.DateTime(timezone=True), nullable=True)
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False)
    updated_at = sa.Column(sa.DateTime(timezone=True), nullable=False)

    __table_args__ = (
        sa.UniqueConstraint("periodo", name="uq_periodos_fiscales_periodo"),
        sa.Index("ix_periodos_fiscales_anio_fiscal", "anio_fiscal"),
    )

    declaraciones_juradas = relationship("DeclaracionJurada", back_populates="periodo_fiscal")
