import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import DestinoRegComprobante

_vc = lambda obj: [e.value for e in obj]  # noqa: E731


class ImputacionFiscal(Base):
    __tablename__ = "imputaciones_fiscales"

    id = sa.Column(UUID(as_uuid=True), primary_key=True)
    comprobante_id = sa.Column(
        UUID(as_uuid=True),
        sa.ForeignKey("comprobantes.id", name="fk_imputaciones_fiscales_comprobante_id", ondelete="RESTRICT"),
        nullable=False,
    )
    categoria_irp_id = sa.Column(
        UUID(as_uuid=True),
        sa.ForeignKey("categorias_irp.id", name="fk_imputaciones_fiscales_categoria_irp_id", ondelete="RESTRICT"),
        nullable=False,
    )
    imputa_iva_credito = sa.Column(sa.Boolean, nullable=False)
    iva_credito_porcentaje = sa.Column(sa.Numeric(5, 2), nullable=False)
    iva_credito_monto = sa.Column(sa.BigInteger, nullable=False)
    imputa_irp = sa.Column(sa.Boolean, nullable=False)
    destino_reg_comprobante = sa.Column(
        sa.Enum(DestinoRegComprobante, values_callable=_vc, name="destino_reg_comprobante"),
        nullable=False,
    )
    a_nombre_de = sa.Column(sa.String(100), nullable=True)
    rectificado = sa.Column(sa.Boolean, nullable=False, default=False)
    fecha_rectificacion = sa.Column(sa.DateTime(timezone=True), nullable=True)
    notas_rectificacion = sa.Column(sa.Text, nullable=True)
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False)
    updated_at = sa.Column(sa.DateTime(timezone=True), nullable=False)

    __table_args__ = (
        sa.UniqueConstraint("comprobante_id", name="uq_imputaciones_fiscales_comprobante_id"),
    )

    comprobante = relationship("Comprobante", back_populates="imputacion_fiscal")
    categoria_irp = relationship("CategoriaIRP", back_populates="imputaciones_fiscales")
