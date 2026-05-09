import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import SyncStatus, TipoContacto, TipoContribuyente

_vc = lambda obj: [e.value for e in obj]  # noqa: E731


class Contacto(Base):
    __tablename__ = "contactos"

    id = sa.Column(UUID(as_uuid=True), primary_key=True)
    ruc = sa.Column(sa.String(15), nullable=False)
    razon_social = sa.Column(sa.String(200), nullable=False)
    nombre_fantasia = sa.Column(sa.String(200), nullable=True)
    tipo = sa.Column(
        sa.Enum(TipoContacto, values_callable=_vc, name="tipo_contacto"),
        nullable=False,
    )
    tipo_contribuyente = sa.Column(
        sa.Enum(TipoContribuyente, values_callable=_vc, name="tipo_contribuyente"),
        nullable=True,
    )
    telefono = sa.Column(sa.String(20), nullable=True)
    email = sa.Column(sa.String(100), nullable=True)
    direccion = sa.Column(sa.Text, nullable=True)
    notas = sa.Column(sa.Text, nullable=True)
    es_frecuente = sa.Column(sa.Boolean, nullable=False, default=False)
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False)
    updated_at = sa.Column(sa.DateTime(timezone=True), nullable=False)
    deleted_at = sa.Column(sa.DateTime(timezone=True), nullable=True)
    sync_status = sa.Column(
        sa.Enum(SyncStatus, values_callable=_vc, name="sync_status"),
        nullable=False,
    )
    device_id = sa.Column(sa.String(50), nullable=True)

    __table_args__ = (
        sa.UniqueConstraint("ruc", name="uq_contactos_ruc"),
        sa.Index("ix_contactos_tipo", "tipo"),
    )

    comprobantes = relationship("Comprobante", back_populates="contacto")
    ingresos = relationship("Ingreso", back_populates="contacto")
