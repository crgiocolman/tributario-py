from datetime import date, datetime

from pydantic import BaseModel


class IVAMes(BaseModel):
    periodo: str
    iva_debito: int
    iva_credito_utilizado: int
    saldo_iva: int
    ventas_gravadas_10: int
    ventas_gravadas_5: int
    ventas_exentas: int
    compras_gravadas_10: int
    compras_gravadas_5: int
    compras_exentas: int
    cantidad_compras: int
    cantidad_ventas: int
    f120_presentado: bool


class IVAMensualOut(BaseModel):
    anio_fiscal: int
    meses: list[IVAMes]
    total_iva_debito: int
    total_iva_credito: int
    saldo_acumulado: int


class TramoIRP(BaseModel):
    base: int
    impuesto: int


class ImpuestoProyectado(BaseModel):
    tramo_8_porciento: TramoIRP
    tramo_9_porciento: TramoIRP
    tramo_10_porciento: TramoIRP
    total: int


class IRPProyeccionOut(BaseModel):
    anio_fiscal: int
    ejercicio_inicio: date
    ejercicio_fin: date
    ingresos_brutos_acumulados: int
    ingresos_computables_irp: int
    egresos_deducibles_acumulados: int
    egresos_por_categoria: dict[str, int]
    renta_neta_actual: int
    renta_neta_proyectada_anual: int
    impuesto_proyectado: ImpuestoProyectado
    reserva_mensual_sugerida: int
    meses_transcurridos: int
    meses_restantes: int


class VencimientoItem(BaseModel):
    periodo: str
    formulario: str
    vencimiento: date
    dias_restantes: int
    presentado: bool
    fecha_presentacion: datetime | None = None


class VencimientosOut(BaseModel):
    items: list[VencimientoItem]


class EgresoCategoria(BaseModel):
    codigo: str
    nombre: str
    total: int
    cantidad_comprobantes: int


class EgresosPorCategoriaOut(BaseModel):
    anio_fiscal: int
    egresos: list[EgresoCategoria]
    total_general: int


class DashboardResumenIVA(BaseModel):
    periodos_con_datos: int
    iva_debito_ytd: int
    iva_credito_ytd: int
    saldo_ytd: int
    periodos_pendientes_f120: int


class DashboardResumenIRP(BaseModel):
    acumulado_computable: int
    umbral_irp: int
    porcentaje_umbral: float
    superado_umbral: bool
    impuesto_estimado: int


class DashboardOut(BaseModel):
    anio_fiscal: int
    fecha_generacion: datetime
    resumen_iva: DashboardResumenIVA
    resumen_irp: DashboardResumenIRP
    proximos_vencimientos: list[VencimientoItem]
    comprobantes_mes_actual: int


# --- Exportación ---


class F120Ventas(BaseModel):
    gravadas_10: int
    iva_debito_10: int
    gravadas_5: int
    iva_debito_5: int
    exentas: int
    total_iva_debito: int


class F120Compras(BaseModel):
    gravadas_10: int
    iva_credito_10_utilizado: int
    gravadas_5: int
    iva_credito_5_utilizado: int
    exentas: int
    total_iva_credito_utilizado: int


class F120Liquidacion(BaseModel):
    iva_debito: int
    iva_credito: int
    saldo: int
    a_pagar: int
    saldo_a_favor: int


class F120ResumenOut(BaseModel):
    periodo: str
    ruc: str
    formulario: str = "F120"
    ventas: F120Ventas
    compras: F120Compras
    liquidacion: F120Liquidacion


class F515IngresoDetalle(BaseModel):
    salarios_brutos: int
    aporte_ips: int
    aguinaldo_exonerado: int
    honorarios_profesionales: int
    otros_ingresos: int
    total_computable_irp: int


class F515EgresoCategoria(BaseModel):
    total: int
    cantidad_comprobantes: int


class F515Liquidacion(BaseModel):
    tramo_8: TramoIRP
    tramo_9: TramoIRP
    tramo_10: TramoIRP
    total_impuesto: int
    retenciones_sufridas: int
    saldo_a_pagar: int


class F515ResumenOut(BaseModel):
    anio_fiscal: int
    ruc: str
    formulario: str = "F515"
    ejercicio_inicio: date
    ejercicio_fin: date
    ingresos: F515IngresoDetalle
    egresos_deducibles: dict[str, F515EgresoCategoria]
    total_egresos_deducibles: int
    renta_neta: int
    liquidacion_irp: F515Liquidacion
