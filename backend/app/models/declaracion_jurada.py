import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import EstadoDJ, Formulario

_vc = lambda obj: [e.value for e in obj]  # noqa: E731


class DeclaracionJurada(Base):
    __tablename__ = "declaraciones_juradas"

    id = sa.Column(UUID(as_uuid=True), primary_key=True)
    periodo_fiscal_id = sa.Column(
        UUID(as_uuid=True),
        sa.ForeignKey("periodos_fiscales.id", name="fk_declaraciones_juradas_periodo_fiscal_id", ondelete="RESTRICT"),
        nullable=True,
    )
    formulario = sa.Column(
        sa.Enum(Formulario, values_callable=_vc, name="formulario"),
        nullable=False,
    )
    periodo = sa.Column(sa.String(7), nullable=False)
    numero_orden = sa.Column(sa.String(20), nullable=True)
    fecha_presentacion = sa.Column(sa.DateTime(timezone=True), nullable=False)
    es_rectificativa = sa.Column(sa.Boolean, nullable=False, default=False)
    rectifica_a = sa.Column(
        UUID(as_uuid=True),
        sa.ForeignKey(
            "declaraciones_juradas.id",
            name="fk_declaraciones_juradas_rectifica_a",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        nullable=True,
    )
    monto_impuesto = sa.Column(sa.BigInteger, nullable=False)
    monto_multa = sa.Column(sa.BigInteger, nullable=False)
    monto_intereses = sa.Column(sa.BigInteger, nullable=False)
    monto_mora = sa.Column(sa.BigInteger, nullable=False)
    monto_total_pagado = sa.Column(sa.BigInteger, nullable=False)
    fecha_pago = sa.Column(sa.DateTime(timezone=True), nullable=True)
    estado = sa.Column(
        sa.Enum(EstadoDJ, values_callable=_vc, name="estado_dj"),
        nullable=False,
    )
    notas = sa.Column(sa.Text, nullable=True)
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False)
    updated_at = sa.Column(sa.DateTime(timezone=True), nullable=False)

    periodo_fiscal = relationship("PeriodoFiscal", back_populates="declaraciones_juradas")
    dj_original = relationship("DeclaracionJurada", remote_side="DeclaracionJurada.id", foreign_keys=[rectifica_a])
