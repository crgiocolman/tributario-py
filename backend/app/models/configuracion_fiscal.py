import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class ConfiguracionFiscal(Base):
    __tablename__ = "configuracion_fiscal"

    id = sa.Column(UUID(as_uuid=True), primary_key=True)
    anio_fiscal = sa.Column(sa.Integer, nullable=False)
    ruc = sa.Column(sa.String(15), nullable=False)
    razon_social = sa.Column(sa.String(200), nullable=False)
    ultimo_digito_ruc = sa.Column(sa.Integer, nullable=False)
    umbral_irp = sa.Column(sa.BigInteger, nullable=False)
    tramo_irp_1_hasta = sa.Column(sa.BigInteger, nullable=False)
    tramo_irp_1_tasa = sa.Column(sa.Numeric(4, 2), nullable=False)
    tramo_irp_2_hasta = sa.Column(sa.BigInteger, nullable=False)
    tramo_irp_2_tasa = sa.Column(sa.Numeric(4, 2), nullable=False)
    tramo_irp_3_tasa = sa.Column(sa.Numeric(4, 2), nullable=False)
    tasa_iva_general = sa.Column(sa.Numeric(4, 2), nullable=False)
    tasa_iva_reducida = sa.Column(sa.Numeric(4, 2), nullable=False)
    multa_dj_determinativa = sa.Column(sa.BigInteger, nullable=False)
    multa_dj_informativa = sa.Column(sa.BigInteger, nullable=False)
    tasa_interes_diario = sa.Column(sa.Numeric(6, 4), nullable=False)
    fecha_inicio_ejercicio = sa.Column(sa.Date, nullable=False)
    fecha_fin_ejercicio = sa.Column(sa.Date, nullable=False)
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False)
    updated_at = sa.Column(sa.DateTime(timezone=True), nullable=False)

    __table_args__ = (
        sa.UniqueConstraint("anio_fiscal", name="uq_configuracion_fiscal_anio_fiscal"),
    )
