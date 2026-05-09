import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import DestinoRegComprobante

_vc = lambda obj: [e.value for e in obj]  # noqa: E731


class ReglaImputacion(Base):
    __tablename__ = "reglas_imputacion"

    id = sa.Column(UUID(as_uuid=True), primary_key=True)
    categoria_irp_id = sa.Column(
        UUID(as_uuid=True),
        sa.ForeignKey("categorias_irp.id", name="fk_reglas_imputacion_categoria_irp_id", ondelete="RESTRICT"),
        nullable=False,
    )
    imputa_iva_credito = sa.Column(sa.Boolean, nullable=False)
    imputa_iva_credito_porcentaje = sa.Column(sa.Numeric(5, 2), nullable=True)
    imputa_irp = sa.Column(sa.Boolean, nullable=False)
    destino_reg_comprobante = sa.Column(
        sa.Enum(DestinoRegComprobante, values_callable=_vc, name="destino_reg_comprobante"),
        nullable=False,
    )
    notas = sa.Column(sa.Text, nullable=True)

    categoria_irp = relationship("CategoriaIRP", back_populates="regla_imputacion")
