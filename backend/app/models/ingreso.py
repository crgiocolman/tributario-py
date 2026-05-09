import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import SyncStatus, TipoIngreso

_vc = lambda obj: [e.value for e in obj]  # noqa: E731


class Ingreso(Base):
    __tablename__ = "ingresos"

    id = sa.Column(UUID(as_uuid=True), primary_key=True)
    comprobante_id = sa.Column(
        UUID(as_uuid=True),
        sa.ForeignKey("comprobantes.id", name="fk_ingresos_comprobante_id", ondelete="RESTRICT"),
        nullable=True,
    )
    contacto_id = sa.Column(
        UUID(as_uuid=True),
        sa.ForeignKey("contactos.id", name="fk_ingresos_contacto_id", ondelete="RESTRICT"),
        nullable=False,
    )
    tipo_ingreso = sa.Column(
        sa.Enum(TipoIngreso, values_callable=_vc, name="tipo_ingreso"),
        nullable=False,
    )
    periodo_devengado = sa.Column(sa.String(7), nullable=False)
    fecha_percepcion = sa.Column(sa.Date, nullable=False)
    monto_bruto = sa.Column(sa.BigInteger, nullable=False)
    aporte_ips_trabajador = sa.Column(sa.BigInteger, nullable=False)
    otros_descuentos = sa.Column(sa.BigInteger, nullable=False)
    monto_exonerado = sa.Column(sa.BigInteger, nullable=False)
    monto_computable_irp = sa.Column(sa.BigInteger, nullable=False)
    es_gravado_irp = sa.Column(sa.Boolean, nullable=False)
    acumulado_anual = sa.Column(sa.BigInteger, nullable=True)
    notas = sa.Column(sa.Text, nullable=True)
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False)
    updated_at = sa.Column(sa.DateTime(timezone=True), nullable=False)
    deleted_at = sa.Column(sa.DateTime(timezone=True), nullable=True)
    sync_status = sa.Column(
        sa.Enum(SyncStatus, values_callable=_vc, name="sync_status"),
        nullable=False,
    )
    device_id = sa.Column(sa.String(50), nullable=True)

    comprobante = relationship("Comprobante", back_populates="ingresos")
    contacto = relationship("Contacto", back_populates="ingresos")
