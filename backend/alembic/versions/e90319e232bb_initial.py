"""initial

Revision ID: e90319e232bb
Revises:
Create Date: 2026-05-09 17:04:07.677907

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM


revision: str = 'e90319e232bb'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _enum(name, *values):
    # PG_ENUM en vez de sa.Enum: sa.Enum pierde create_type=False al adaptarse al dialecto PG.
    return PG_ENUM(*values, name=name, create_type=False)


def upgrade() -> None:
    # --- Enum types (created explicitly so each type is only ever issued once) ---
    op.execute("CREATE TYPE sync_status AS ENUM ('pending', 'synced', 'conflict')")
    op.execute("CREATE TYPE tipo_contacto AS ENUM ('cliente', 'proveedor', 'ambos')")
    op.execute("CREATE TYPE tipo_contribuyente AS ENUM ('persona_fisica', 'persona_juridica')")
    op.execute("CREATE TYPE tipo_operacion AS ENUM ('compra', 'venta')")
    op.execute("CREATE TYPE tipo_comprobante AS ENUM ('factura', 'autofactura', 'ticket', 'nota_credito', 'nota_debito', 'boleta_resimple', 'liquidacion_salario')")
    op.execute("CREATE TYPE forma_emision AS ENUM ('electronica', 'virtual', 'preimpresa', 'autoimpresor', 'no_aplica')")
    op.execute("CREATE TYPE condicion AS ENUM ('contado', 'credito')")
    op.execute("CREATE TYPE forma_pago AS ENUM ('efectivo', 'transferencia', 'tarjeta_credito', 'tarjeta_debito', 'cheque', 'mixto')")
    op.execute("CREATE TYPE cargado_marangatu AS ENUM ('si', 'no', 'auto')")
    op.execute("CREATE TYPE destino_reg_comprobante AS ENUM ('iva', 'irp_rsp', 'no_imputar')")
    op.execute("CREATE TYPE tipo_ingreso AS ENUM ('salario', 'aguinaldo', 'vacaciones', 'liquidacion_final', 'honorarios', 'otros')")
    op.execute("CREATE TYPE formulario AS ENUM ('f120', 'f515', 'reg_comprobantes')")
    op.execute("CREATE TYPE estado_dj AS ENUM ('presentada', 'pagada', 'pendiente', 'vencida')")

    # --- Tables ---
    op.create_table('categorias_irp',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('codigo', sa.String(length=30), nullable=False),
    sa.Column('nombre', sa.String(length=100), nullable=False),
    sa.Column('descripcion', sa.Text(), nullable=True),
    sa.Column('articulo_ley', sa.String(length=50), nullable=True),
    sa.Column('limite_porcentaje', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('orden', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('codigo', name='uq_categorias_irp_codigo')
    )
    op.create_table('configuracion_fiscal',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('anio_fiscal', sa.Integer(), nullable=False),
    sa.Column('ruc', sa.String(length=15), nullable=False),
    sa.Column('razon_social', sa.String(length=200), nullable=False),
    sa.Column('ultimo_digito_ruc', sa.Integer(), nullable=False),
    sa.Column('umbral_irp', sa.BigInteger(), nullable=False),
    sa.Column('tramo_irp_1_hasta', sa.BigInteger(), nullable=False),
    sa.Column('tramo_irp_1_tasa', sa.Numeric(precision=4, scale=2), nullable=False),
    sa.Column('tramo_irp_2_hasta', sa.BigInteger(), nullable=False),
    sa.Column('tramo_irp_2_tasa', sa.Numeric(precision=4, scale=2), nullable=False),
    sa.Column('tramo_irp_3_tasa', sa.Numeric(precision=4, scale=2), nullable=False),
    sa.Column('tasa_iva_general', sa.Numeric(precision=4, scale=2), nullable=False),
    sa.Column('tasa_iva_reducida', sa.Numeric(precision=4, scale=2), nullable=False),
    sa.Column('multa_dj_determinativa', sa.BigInteger(), nullable=False),
    sa.Column('multa_dj_informativa', sa.BigInteger(), nullable=False),
    sa.Column('tasa_interes_diario', sa.Numeric(precision=6, scale=4), nullable=False),
    sa.Column('fecha_inicio_ejercicio', sa.Date(), nullable=False),
    sa.Column('fecha_fin_ejercicio', sa.Date(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('anio_fiscal', name='uq_configuracion_fiscal_anio_fiscal')
    )
    op.create_table('contactos',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('ruc', sa.String(length=15), nullable=False),
    sa.Column('razon_social', sa.String(length=200), nullable=False),
    sa.Column('nombre_fantasia', sa.String(length=200), nullable=True),
    sa.Column('tipo', _enum('tipo_contacto', 'cliente', 'proveedor', 'ambos'), nullable=False),
    sa.Column('tipo_contribuyente', _enum('tipo_contribuyente', 'persona_fisica', 'persona_juridica'), nullable=True),
    sa.Column('telefono', sa.String(length=20), nullable=True),
    sa.Column('email', sa.String(length=100), nullable=True),
    sa.Column('direccion', sa.Text(), nullable=True),
    sa.Column('notas', sa.Text(), nullable=True),
    sa.Column('es_frecuente', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('sync_status', _enum('sync_status', 'pending', 'synced', 'conflict'), nullable=False),
    sa.Column('device_id', sa.String(length=50), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('ruc', name='uq_contactos_ruc')
    )
    op.create_index('ix_contactos_tipo', 'contactos', ['tipo'], unique=False)
    op.create_table('periodos_fiscales',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('periodo', sa.String(length=7), nullable=False),
    sa.Column('anio_fiscal', sa.Integer(), nullable=False),
    sa.Column('total_ventas_gravadas_10', sa.BigInteger(), nullable=False),
    sa.Column('total_ventas_gravadas_5', sa.BigInteger(), nullable=False),
    sa.Column('total_ventas_exentas', sa.BigInteger(), nullable=False),
    sa.Column('total_iva_debito', sa.BigInteger(), nullable=False),
    sa.Column('total_compras_gravadas_10', sa.BigInteger(), nullable=False),
    sa.Column('total_compras_gravadas_5', sa.BigInteger(), nullable=False),
    sa.Column('total_compras_exentas', sa.BigInteger(), nullable=False),
    sa.Column('total_iva_credito_utilizado', sa.BigInteger(), nullable=False),
    sa.Column('saldo_iva', sa.BigInteger(), nullable=False),
    sa.Column('total_ingresos_irp', sa.BigInteger(), nullable=False),
    sa.Column('total_egresos_irp', sa.BigInteger(), nullable=False),
    sa.Column('cantidad_comprobantes_compras', sa.Integer(), nullable=False),
    sa.Column('cantidad_comprobantes_ventas', sa.Integer(), nullable=False),
    sa.Column('f120_presentado', sa.Boolean(), nullable=False),
    sa.Column('f120_fecha_presentacion', sa.DateTime(timezone=True), nullable=True),
    sa.Column('reg_comprobantes_presentado', sa.Boolean(), nullable=False),
    sa.Column('reg_comprobantes_fecha', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('periodo', name='uq_periodos_fiscales_periodo')
    )
    op.create_index('ix_periodos_fiscales_anio_fiscal', 'periodos_fiscales', ['anio_fiscal'], unique=False)
    op.create_table('comprobantes',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('contacto_id', sa.UUID(), nullable=False),
    sa.Column('tipo_operacion', _enum('tipo_operacion', 'compra', 'venta'), nullable=False),
    sa.Column('tipo_comprobante', _enum('tipo_comprobante', 'factura', 'autofactura', 'ticket', 'nota_credito', 'nota_debito', 'boleta_resimple', 'liquidacion_salario'), nullable=False),
    sa.Column('forma_emision', _enum('forma_emision', 'electronica', 'virtual', 'preimpresa', 'autoimpresor', 'no_aplica'), nullable=False),
    sa.Column('numero_timbrado', sa.String(length=20), nullable=True),
    sa.Column('numero_comprobante', sa.String(length=25), nullable=True),
    sa.Column('fecha_emision', sa.Date(), nullable=False),
    sa.Column('fecha_percepcion', sa.Date(), nullable=True),
    sa.Column('condicion', _enum('condicion', 'contado', 'credito'), nullable=False),
    sa.Column('moneda', sa.String(length=3), nullable=False),
    sa.Column('tipo_cambio', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('monto_exento', sa.BigInteger(), nullable=False),
    sa.Column('monto_gravado_5', sa.BigInteger(), nullable=False),
    sa.Column('iva_5', sa.BigInteger(), nullable=False),
    sa.Column('monto_gravado_10', sa.BigInteger(), nullable=False),
    sa.Column('iva_10', sa.BigInteger(), nullable=False),
    sa.Column('total', sa.BigInteger(), nullable=False),
    sa.Column('forma_pago', _enum('forma_pago', 'efectivo', 'transferencia', 'tarjeta_credito', 'tarjeta_debito', 'cheque', 'mixto'), nullable=True),
    sa.Column('concepto', sa.Text(), nullable=True),
    sa.Column('periodo_fiscal', sa.String(length=7), nullable=False),
    sa.Column('cargado_marangatu', _enum('cargado_marangatu', 'si', 'no', 'auto'), nullable=False),
    sa.Column('notas', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('sync_status', _enum('sync_status', 'pending', 'synced', 'conflict'), nullable=False),
    sa.Column('device_id', sa.String(length=50), nullable=True),
    sa.ForeignKeyConstraint(['contacto_id'], ['contactos.id'], name='fk_comprobantes_contacto_id', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('numero_timbrado', 'numero_comprobante', name='uq_comprobantes_timbrado_numero')
    )
    op.create_index('ix_comprobantes_contacto_id', 'comprobantes', ['contacto_id'], unique=False)
    op.create_index('ix_comprobantes_fecha_emision', 'comprobantes', ['fecha_emision'], unique=False)
    op.create_index('ix_comprobantes_periodo_fiscal', 'comprobantes', ['periodo_fiscal'], unique=False)
    op.create_index('ix_comprobantes_tipo_operacion', 'comprobantes', ['tipo_operacion'], unique=False)
    op.create_table('declaraciones_juradas',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('periodo_fiscal_id', sa.UUID(), nullable=True),
    sa.Column('formulario', _enum('formulario', 'f120', 'f515', 'reg_comprobantes'), nullable=False),
    sa.Column('periodo', sa.String(length=7), nullable=False),
    sa.Column('numero_orden', sa.String(length=20), nullable=True),
    sa.Column('fecha_presentacion', sa.DateTime(timezone=True), nullable=False),
    sa.Column('es_rectificativa', sa.Boolean(), nullable=False),
    sa.Column('rectifica_a', sa.UUID(), nullable=True),
    sa.Column('monto_impuesto', sa.BigInteger(), nullable=False),
    sa.Column('monto_multa', sa.BigInteger(), nullable=False),
    sa.Column('monto_intereses', sa.BigInteger(), nullable=False),
    sa.Column('monto_mora', sa.BigInteger(), nullable=False),
    sa.Column('monto_total_pagado', sa.BigInteger(), nullable=False),
    sa.Column('fecha_pago', sa.DateTime(timezone=True), nullable=True),
    sa.Column('estado', _enum('estado_dj', 'presentada', 'pagada', 'pendiente', 'vencida'), nullable=False),
    sa.Column('notas', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['periodo_fiscal_id'], ['periodos_fiscales.id'], name='fk_declaraciones_juradas_periodo_fiscal_id', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['rectifica_a'], ['declaraciones_juradas.id'], name='fk_declaraciones_juradas_rectifica_a', ondelete='RESTRICT', use_alter=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('reglas_imputacion',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('categoria_irp_id', sa.UUID(), nullable=False),
    sa.Column('imputa_iva_credito', sa.Boolean(), nullable=False),
    sa.Column('imputa_iva_credito_porcentaje', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('imputa_irp', sa.Boolean(), nullable=False),
    sa.Column('destino_reg_comprobante', _enum('destino_reg_comprobante', 'iva', 'irp_rsp', 'no_imputar'), nullable=False),
    sa.Column('notas', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['categoria_irp_id'], ['categorias_irp.id'], name='fk_reglas_imputacion_categoria_irp_id', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('archivos_adjuntos',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('comprobante_id', sa.UUID(), nullable=False),
    sa.Column('nombre_archivo', sa.String(length=255), nullable=False),
    sa.Column('tipo_mime', sa.String(length=50), nullable=False),
    sa.Column('tamano_bytes', sa.BigInteger(), nullable=False),
    sa.Column('ruta_almacenamiento', sa.Text(), nullable=False),
    sa.Column('hash_sha256', sa.String(length=64), nullable=True),
    sa.Column('sync_status', _enum('sync_status', 'pending', 'synced', 'conflict'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['comprobante_id'], ['comprobantes.id'], name='fk_archivos_adjuntos_comprobante_id', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('imputaciones_fiscales',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('comprobante_id', sa.UUID(), nullable=False),
    sa.Column('categoria_irp_id', sa.UUID(), nullable=False),
    sa.Column('imputa_iva_credito', sa.Boolean(), nullable=False),
    sa.Column('iva_credito_porcentaje', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('iva_credito_monto', sa.BigInteger(), nullable=False),
    sa.Column('imputa_irp', sa.Boolean(), nullable=False),
    sa.Column('destino_reg_comprobante', _enum('destino_reg_comprobante', 'iva', 'irp_rsp', 'no_imputar'), nullable=False),
    sa.Column('a_nombre_de', sa.String(length=100), nullable=True),
    sa.Column('rectificado', sa.Boolean(), nullable=False),
    sa.Column('fecha_rectificacion', sa.DateTime(timezone=True), nullable=True),
    sa.Column('notas_rectificacion', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['categoria_irp_id'], ['categorias_irp.id'], name='fk_imputaciones_fiscales_categoria_irp_id', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['comprobante_id'], ['comprobantes.id'], name='fk_imputaciones_fiscales_comprobante_id', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('comprobante_id', name='uq_imputaciones_fiscales_comprobante_id')
    )
    op.create_table('ingresos',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('comprobante_id', sa.UUID(), nullable=True),
    sa.Column('contacto_id', sa.UUID(), nullable=False),
    sa.Column('tipo_ingreso', _enum('tipo_ingreso', 'salario', 'aguinaldo', 'vacaciones', 'liquidacion_final', 'honorarios', 'otros'), nullable=False),
    sa.Column('periodo_devengado', sa.String(length=7), nullable=False),
    sa.Column('fecha_percepcion', sa.Date(), nullable=False),
    sa.Column('monto_bruto', sa.BigInteger(), nullable=False),
    sa.Column('aporte_ips_trabajador', sa.BigInteger(), nullable=False),
    sa.Column('otros_descuentos', sa.BigInteger(), nullable=False),
    sa.Column('monto_exonerado', sa.BigInteger(), nullable=False),
    sa.Column('monto_computable_irp', sa.BigInteger(), nullable=False),
    sa.Column('es_gravado_irp', sa.Boolean(), nullable=False),
    sa.Column('acumulado_anual', sa.BigInteger(), nullable=True),
    sa.Column('notas', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('sync_status', _enum('sync_status', 'pending', 'synced', 'conflict'), nullable=False),
    sa.Column('device_id', sa.String(length=50), nullable=True),
    sa.ForeignKeyConstraint(['comprobante_id'], ['comprobantes.id'], name='fk_ingresos_comprobante_id', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['contacto_id'], ['contactos.id'], name='fk_ingresos_contacto_id', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('ingresos')
    op.drop_table('imputaciones_fiscales')
    op.drop_table('archivos_adjuntos')
    op.drop_table('reglas_imputacion')
    op.drop_table('declaraciones_juradas')
    op.drop_index('ix_comprobantes_tipo_operacion', table_name='comprobantes')
    op.drop_index('ix_comprobantes_periodo_fiscal', table_name='comprobantes')
    op.drop_index('ix_comprobantes_fecha_emision', table_name='comprobantes')
    op.drop_index('ix_comprobantes_contacto_id', table_name='comprobantes')
    op.drop_table('comprobantes')
    op.drop_index('ix_periodos_fiscales_anio_fiscal', table_name='periodos_fiscales')
    op.drop_table('periodos_fiscales')
    op.drop_index('ix_contactos_tipo', table_name='contactos')
    op.drop_table('contactos')
    op.drop_table('configuracion_fiscal')
    op.drop_table('categorias_irp')

    op.execute("DROP TYPE IF EXISTS tipo_ingreso")
    op.execute("DROP TYPE IF EXISTS destino_reg_comprobante")
    op.execute("DROP TYPE IF EXISTS cargado_marangatu")
    op.execute("DROP TYPE IF EXISTS forma_pago")
    op.execute("DROP TYPE IF EXISTS condicion")
    op.execute("DROP TYPE IF EXISTS forma_emision")
    op.execute("DROP TYPE IF EXISTS tipo_comprobante")
    op.execute("DROP TYPE IF EXISTS tipo_operacion")
    op.execute("DROP TYPE IF EXISTS tipo_contribuyente")
    op.execute("DROP TYPE IF EXISTS tipo_contacto")
    op.execute("DROP TYPE IF EXISTS sync_status")
    op.execute("DROP TYPE IF EXISTS formulario")
    op.execute("DROP TYPE IF EXISTS estado_dj")
