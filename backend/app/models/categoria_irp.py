import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class CategoriaIRP(Base):
    __tablename__ = "categorias_irp"

    id = sa.Column(UUID(as_uuid=True), primary_key=True)
    codigo = sa.Column(sa.String(30), nullable=False)
    nombre = sa.Column(sa.String(100), nullable=False)
    descripcion = sa.Column(sa.Text, nullable=True)
    articulo_ley = sa.Column(sa.String(50), nullable=True)
    limite_porcentaje = sa.Column(sa.Numeric(5, 2), nullable=True)
    activo = sa.Column(sa.Boolean, nullable=False, default=True)
    orden = sa.Column(sa.Integer, nullable=False)

    __table_args__ = (
        sa.UniqueConstraint("codigo", name="uq_categorias_irp_codigo"),
    )

    regla_imputacion = relationship("ReglaImputacion", back_populates="categoria_irp", uselist=False)
    imputaciones_fiscales = relationship("ImputacionFiscal", back_populates="categoria_irp")
