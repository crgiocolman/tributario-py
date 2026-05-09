import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import SyncStatus

_vc = lambda obj: [e.value for e in obj]  # noqa: E731


class ArchivoAdjunto(Base):
    __tablename__ = "archivos_adjuntos"

    id = sa.Column(UUID(as_uuid=True), primary_key=True)
    comprobante_id = sa.Column(
        UUID(as_uuid=True),
        sa.ForeignKey("comprobantes.id", name="fk_archivos_adjuntos_comprobante_id", ondelete="RESTRICT"),
        nullable=False,
    )
    nombre_archivo = sa.Column(sa.String(255), nullable=False)
    tipo_mime = sa.Column(sa.String(50), nullable=False)
    tamano_bytes = sa.Column(sa.BigInteger, nullable=False)
    ruta_almacenamiento = sa.Column(sa.Text, nullable=False)
    hash_sha256 = sa.Column(sa.String(64), nullable=True)
    sync_status = sa.Column(
        sa.Enum(SyncStatus, values_callable=_vc, name="sync_status"),
        nullable=False,
    )
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False)

    comprobante = relationship("Comprobante", back_populates="archivos_adjuntos")
