from enum import Enum


class SyncStatus(str, Enum):
    PENDING = "pending"
    SYNCED = "synced"
    CONFLICT = "conflict"


class TipoContacto(str, Enum):
    CLIENTE = "cliente"
    PROVEEDOR = "proveedor"
    AMBOS = "ambos"


class TipoContribuyente(str, Enum):
    PERSONA_FISICA = "persona_fisica"
    PERSONA_JURIDICA = "persona_juridica"


class TipoOperacion(str, Enum):
    COMPRA = "compra"
    VENTA = "venta"


class TipoComprobante(str, Enum):
    FACTURA = "factura"
    AUTOFACTURA = "autofactura"
    TICKET = "ticket"
    NOTA_CREDITO = "nota_credito"
    NOTA_DEBITO = "nota_debito"
    BOLETA_RESIMPLE = "boleta_resimple"
    LIQUIDACION_SALARIO = "liquidacion_salario"


class FormaEmision(str, Enum):
    ELECTRONICA = "electronica"
    VIRTUAL = "virtual"
    PREIMPRESA = "preimpresa"
    AUTOIMPRESOR = "autoimpresor"
    NO_APLICA = "no_aplica"


class Condicion(str, Enum):
    CONTADO = "contado"
    CREDITO = "credito"


class FormaPago(str, Enum):
    EFECTIVO = "efectivo"
    TRANSFERENCIA = "transferencia"
    TARJETA_CREDITO = "tarjeta_credito"
    TARJETA_DEBITO = "tarjeta_debito"
    CHEQUE = "cheque"
    MIXTO = "mixto"


class CargadoMarangatu(str, Enum):
    SI = "si"
    NO = "no"
    AUTO = "auto"


class DestinoRegComprobante(str, Enum):
    IVA = "iva"
    IRP_RSP = "irp_rsp"
    NO_IMPUTAR = "no_imputar"


class TipoIngreso(str, Enum):
    SALARIO = "salario"
    AGUINALDO = "aguinaldo"
    VACACIONES = "vacaciones"
    LIQUIDACION_FINAL = "liquidacion_final"
    HONORARIOS = "honorarios"
    OTROS = "otros"


class Formulario(str, Enum):
    F120 = "f120"
    F515 = "f515"
    REG_COMPROBANTES = "reg_comprobantes"


class EstadoDJ(str, Enum):
    PRESENTADA = "presentada"
    PAGADA = "pagada"
    PENDIENTE = "pendiente"
    VENCIDA = "vencida"
