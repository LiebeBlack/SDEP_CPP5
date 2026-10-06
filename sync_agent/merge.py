"""
Motor de mezcla (funciones puras)

Aquí vive la regla que evita la sobreescritura ciega: **cada campo se decide
por separado** comparando la última escritura conocida de ese campo con la que
llega desde la red, mediante un orden total y determinista.

El orden es la terna ``(actualizado_en, dispositivo, op_id)``:

* ``actualizado_en`` respeta la intención del usuario (lo más reciente gana);
* ``dispositivo`` y ``op_id`` desempatan cuando dos equipos escribieron en el
  mismo instante, de modo que **todos los nodos eligen el mismo ganador** y el
  sistema converge sin importar el orden en que lleguen las operaciones.

Nada se descarta en silencio: cuando dos valores distintos compiten, el
perdedor queda registrado como conflicto para que el administrador lo revise.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from sync_agent.comun import descripcion_valor

# Diferencia por debajo de la cual dos escrituras se consideran simultáneas
# (los relojes de dos equipos nunca están perfectamente sincronizados).
EPSILON_RELOJ = timedelta(seconds=2)

DECISION_APLICAR = "aplicar"
DECISION_IGNORAR_ANTIGUA = "ignorar_antigua"
DECISION_IGNORAR_IDENTICA = "ignorar_identica"
DECISION_REPETIDA = "repetida"

BORRAR = "borrar"
MANTENER_BORRADO = "mantener_borrado"
REVIVIR = "revivir"
IGNORAR_BORRADO = "ignorar"

GANADOR_LOCAL = "local"
GANADOR_REMOTO = "remoto"

REGLA_MAS_RECIENTE = "escritura_mas_reciente"
REGLA_SIMULTANEA = "escritura_simultanea_desempate_dispositivo"
REGLA_CAMPO_SENSIBLE = "campo_sensible_revisar"
REGLA_REVIVE = "actualizacion_posterior_al_borrado"
REGLA_BORRADO_TARDIO = "borrado_posterior_a_la_actualizacion"
REGLA_ACTUALIZACION_TARDIA = "borrado_posterior_ignora_actualizacion"
REGLA_BORRADO_ANTIGUO = "borrado_antiguo_ignorado"

# Campos cuyo choque se registra siempre, aunque la regla general lo resuelva
# sola: son importes y condiciones económicas que conviene poder auditar.
CAMPOS_SENSIBLES: dict[str, tuple[str, ...]] = {
    "empleados": ("salario_base",),
    "pagos": (
        "monto_bruto",
        "monto_neto",
        "descuentos",
        "bonificaciones",
        "horas_extra",
        "salario_base",
        "deduccion_seguro",
        "deduccion_pension",
        "deduccion_impuesto",
        "otras_deducciones",
        "base_gravable",
        "aguinaldo",
        "bono_vacacional",
    ),
    "contratos": ("salario_pactado", "liquidacion_monto"),
    # Una calificación es un dato académico con consecuencia legal: un choque
    # entre equipos siempre se registra para su revisión, aunque la marca más
    # reciente decida por sí sola qué valor queda vigente.
    "notas_finales": ("calificacion",),
}


@dataclass(frozen=True)
class Marca:
    """Última escritura conocida de un campo (local o remota)"""

    valor: Any
    op_id: str
    dispositivo: str
    actualizado_en: datetime

    def clave(self) -> tuple[datetime, str, str]:
        """Clave de orden total y determinista de la escritura"""
        return (self.actualizado_en, self.dispositivo, self.op_id)

    def es_la_misma_operacion(self, otra: "Marca") -> bool:
        """Indica si ambas marcas proceden de la misma operación"""
        return self.op_id == otra.op_id

    def a_json(self) -> dict[str, Any]:
        """Forma serializable de la marca (para la bandeja de conflictos)"""
        return {
            "valor": self.valor,
            "op_id": self.op_id,
            "dispositivo": self.dispositivo,
            "actualizado_en": self.actualizado_en.isoformat(),
        }


@dataclass(frozen=True)
class Conflicto:
    """Choque real entre dos escrituras, conservado para su revisión"""

    tabla: str
    fila_uuid: str
    campo: str
    valor_local: Any
    valor_remoto: Any
    ganador: str
    regla: str
    op_local_id: str | None = None
    op_remoto_id: str | None = None

    @property
    def resumen(self) -> str:
        """Descripción legible del conflicto"""
        return (
            f"{self.tabla}.{self.campo}: se conservó el valor {self.ganador} "
            f"({descripcion_valor(self.valor_local if self.ganador == GANADOR_LOCAL else self.valor_remoto)}); "
            f"el otro valor ({descripcion_valor(self.valor_remoto if self.ganador == GANADOR_LOCAL else self.valor_local)}) "
            f"queda registrado con la regla «{self.regla}»"
        )


@dataclass(frozen=True)
class VersionFila:
    """Estado conocido de una fila: última escritura y borrado vigente"""

    ultimo_op_id: str | None = None
    actualizado_en: datetime | None = None
    dispositivo: str | None = None
    borrado: bool = False
    borrado_en: datetime | None = None
    borrado_op_id: str | None = None
    borrado_dispositivo: str | None = None

    def marca_ultima(self) -> Marca | None:
        """Marca de la última actualización, si se conoce"""
        if self.ultimo_op_id is None or self.actualizado_en is None:
            return None
        return Marca(
            valor=None,
            op_id=self.ultimo_op_id,
            dispositivo=self.dispositivo or "",
            actualizado_en=self.actualizado_en,
        )

    def marca_borrado(self) -> Marca | None:
        """Marca del borrado vigente, si la fila está borrada"""
        if not self.borrado or self.borrado_en is None:
            return None
        return Marca(
            valor=None,
            op_id=self.borrado_op_id or "",
            dispositivo=self.borrado_dispositivo or "",
            actualizado_en=self.borrado_en,
        )


@dataclass(frozen=True)
class Plan:
    """Resultado de planificar una operación remota sobre una fila"""

    aplicar: dict[str, Any] = field(default_factory=dict)
    marcas: dict[str, Marca] = field(default_factory=dict)
    conflictos: tuple[Conflicto, ...] = ()
    borrar: bool = False
    revivir: bool = False
    motivo: str | None = None

    @property
    def sin_cambios(self) -> bool:
        """Indica si la operación no modifica nada (ya aplicada o superada)"""
        return not self.aplicar and not self.borrar and not self.revivir


def evaluar_reloj(inicial: datetime, final: datetime) -> str:
    """Clasifica la relación entre dos marcas de tiempo"""
    if final - inicial <= EPSILON_RELOJ:
        return REGLA_SIMULTANEA
    return REGLA_MAS_RECIENTE


def decidir_campo(actual: Marca | None, entrante: Marca) -> str:
    """
    Decide si una escritura remota debe aplicarse sobre un campo

    Args:
        actual: Última escritura conocida del campo (None si nunca se tocó)
        entrante: Escritura que llega desde la red

    Returns:
        Una de las constantes DECISION_*
    """
    if actual is None:
        return DECISION_APLICAR
    if entrante.es_la_misma_operacion(actual):
        return DECISION_REPETIDA
    if entrante.valor == actual.valor:
        return DECISION_IGNORAR_IDENTICA
    if entrante.clave() > actual.clave():
        return DECISION_APLICAR
    return DECISION_IGNORAR_ANTIGUA


def planificar_campos(
    tabla: str,
    fila_uuid: str,
    entrantes: dict[str, Marca],
    actuales: dict[str, Marca],
) -> Plan:
    """
    Planifica la escritura de todos los campos de una operación

    La decisión de cada campo es independiente, así que dos equipos que editan
    columnas distintas del mismo registro conservan **ambas** ediciones; solo
    cuando tocan la misma columna hay un ganador y un conflicto registrado.

    Args:
        tabla: Nombre de la tabla
        fila_uuid: Identidad global de la fila
        entrantes: Campos y marcas que llegan en la operación
        actuales: Campos y marcas que ya se conocían localmente

    Returns:
        Plan con los valores a escribir, sus marcas y los conflictos detectados
    """
    aplicar: dict[str, Any] = {}
    marcas: dict[str, Marca] = {}
    conflictos: list[Conflicto] = []
    sensibles = CAMPOS_SENSIBLES.get(tabla, ())

    for campo, entrante in entrantes.items():
        actual = actuales.get(campo)
        decision = decidir_campo(actual, entrante)
        if decision == DECISION_REPETIDA:
            continue
        if decision == DECISION_IGNORAR_IDENTICA:
            # El valor no cambia, pero la marca conocida sí debe avanzar si la
            # escritura entrante es más reciente: conservar la marca vieja
            # permite que una operación intermedia, al llegar fuera de orden,
            # se aplique sobre un valor que el emisor ya había reemplazado.
            if actual is not None and entrante.clave() > actual.clave():
                marcas[campo] = entrante
            continue
        if decision == DECISION_APLICAR:
            aplicar[campo] = entrante.valor
            marcas[campo] = entrante
            if actual is not None and actual.valor != entrante.valor and campo in sensibles:
                conflictos.append(
                    Conflicto(
                        tabla=tabla,
                        fila_uuid=fila_uuid,
                        campo=campo,
                        valor_local=actual.valor,
                        valor_remoto=entrante.valor,
                        ganador=GANADOR_REMOTO,
                        regla=f"{REGLA_CAMPO_SENSIBLE}:{evaluar_reloj(actual.actualizado_en, entrante.actualizado_en)}",
                        op_local_id=actual.op_id,
                        op_remoto_id=entrante.op_id,
                    )
                )
            continue

        # La escritura local es más reciente: se conserva y se registra el
        # valor perdedor para que no desaparezca sin dejar rastro.
        conflictos.append(
            Conflicto(
                tabla=tabla,
                fila_uuid=fila_uuid,
                campo=campo,
                valor_local=actual.valor if actual else None,
                valor_remoto=entrante.valor,
                ganador=GANADOR_LOCAL,
                regla=(
                    evaluar_reloj(entrante.actualizado_en, actual.actualizado_en)
                    if actual
                    else REGLA_MAS_RECIENTE
                ),
                op_local_id=actual.op_id if actual else None,
                op_remoto_id=entrante.op_id,
            )
        )

    return Plan(aplicar=aplicar, marcas=marcas, conflictos=tuple(conflictos))


def decidir_borrado(version: VersionFila | None, entrante: Marca) -> tuple[str, Conflicto | None]:
    """
    Decide si un borrado o una actualización se aplica sobre una fila

    Un borrado es una escritura más: gana el más reciente. Una actualización
    posterior a un borrado revive la fila (y queda registrada), porque perder
    un dato recién editado es peor que resucitar un registro borrado por error.

    Args:
        version: Estado conocido de la fila (None si es nueva)
        entrante: Marca de la operación que llega

    Returns:
        Tupla (decisión, conflicto o None)
    """
    if version is None:
        return BORRAR, None

    marca_borrado = version.marca_borrado()
    if marca_borrado is None:
        return BORRAR, None

    if entrante.es_la_misma_operacion(marca_borrado):
        return IGNORAR_BORRADO, None

    if entrante.clave() >= marca_borrado.clave():
        conflicto = Conflicto(
            tabla="",
            fila_uuid="",
            campo="__borrado__",
            valor_local=True,
            valor_remoto=entrante.valor,
            ganador=GANADOR_REMOTO,
            regla=REGLA_REVIVE,
            op_local_id=marca_borrado.op_id,
            op_remoto_id=entrante.op_id,
        )
        return REVIVIR, conflicto

    conflicto = Conflicto(
        tabla="",
        fila_uuid="",
        campo="__borrado__",
        valor_local=True,
        valor_remoto=entrante.valor,
        ganador=GANADOR_LOCAL,
        regla=REGLA_ACTUALIZACION_TARDIA,
        op_local_id=marca_borrado.op_id,
        op_remoto_id=entrante.op_id,
    )
    return MANTENER_BORRADO, conflicto


def decidir_borrado_sobre_actualizacion(
    version: VersionFila | None, entrante: Marca
) -> tuple[str, Conflicto | None]:
    """
    Decide si un borrado remoto debe aplicarse sobre una fila viva

    Args:
        version: Estado conocido de la fila
        entrante: Marca del borrado que llega

    Returns:
        Tupla (decisión, conflicto o None)
    """
    if version is None:
        return BORRAR, None

    marca_ultima = version.marca_ultima()
    if marca_ultima is None:
        return BORRAR, None
    if entrante.es_la_misma_operacion(marca_ultima):
        return IGNORAR_BORRADO, None
    if entrante.clave() >= marca_ultima.clave():
        return BORRAR, None

    conflicto = Conflicto(
        tabla="",
        fila_uuid="",
        campo="__borrado__",
        valor_local=False,
        valor_remoto=True,
        ganador=GANADOR_LOCAL,
        regla=REGLA_BORRADO_ANTIGUO,
        op_local_id=marca_ultima.op_id,
        op_remoto_id=entrante.op_id,
    )
    return MANTENER_BORRADO, conflicto
