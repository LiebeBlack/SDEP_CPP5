"""
Pruebas del motor de mezcla del agente de sincronización

El motor es puro (no toca la base de datos), así que aquí se verifican las
garantías que sostienen todo lo demás:

* cada campo se decide por separado, de modo que dos equipos que editan
  columnas distintas del mismo registro conservan **ambas** ediciones;
* el orden total ``(momento, dispositivo, operación)`` hace que cualquier
  nodo elija al mismo ganador, sin importar el orden en que lleguen las
  operaciones (convergencia);
* el valor que pierde nunca desaparece: queda como conflicto registrado.
"""

from datetime import datetime, timedelta

from sync_agent.merge import (
    BORRAR,
    DECISION_APLICAR,
    DECISION_IGNORAR_ANTIGUA,
    DECISION_IGNORAR_IDENTICA,
    DECISION_REPETIDA,
    GANADOR_LOCAL,
    GANADOR_REMOTO,
    IGNORAR_BORRADO,
    MANTENER_BORRADO,
    REGLA_CAMPO_SENSIBLE,
    REGLA_REVIVE,
    REVIVIR,
    Marca,
    VersionFila,
    decidir_borrado,
    decidir_borrado_sobre_actualizacion,
    decidir_campo,
    planificar_campos,
)

T0 = datetime(2026, 1, 1, 12, 0, 0)


def _marca(valor, dispositivo="equipo-a", segundos=0, op_id=None):
    """Marca de escritura en un momento concreto (atributos explícitos)"""
    return Marca(
        valor=valor,
        op_id=op_id or f"{dispositivo}-{segundos}",
        dispositivo=dispositivo,
        actualizado_en=T0 + timedelta(seconds=segundos),
    )


class Nodo:
    """
    Estado de mezcla en memoria equivalente al que guarda el agente

    Sirve para simular dos puestos que reciben el mismo conjunto de
    operaciones en órdenes distintos y comprobar que terminan igual.
    """

    def __init__(self):
        self.campos: dict[str, Marca] = {}
        self.conflictos: list = []

    def recibir(self, fila_uuid: str, entrantes: dict[str, Marca], tabla: str = "empleados"):
        plan = planificar_campos(tabla, fila_uuid, entrantes, self.campos)
        self.campos.update(plan.marcas)
        self.conflictos.extend(plan.conflictos)
        return plan

    def valores(self) -> dict:
        return {campo: marca.valor for campo, marca in self.campos.items()}


# ----------------------------------------------------------------------
# Decisión por campo
# ----------------------------------------------------------------------
def test_campo_nuevo_se_aplica_siempre():
    assert decidir_campo(None, _marca("nuevo")) == DECISION_APLICAR


def test_escritura_mas_reciente_gana():
    actual = _marca("viejo", segundos=0)
    entrante = _marca("nuevo", dispositivo="equipo-b", segundos=10)
    assert decidir_campo(actual, entrante) == DECISION_APLICAR


def test_escritura_antigua_se_ignora():
    actual = _marca("reciente", segundos=10)
    entrante = _marca("antigua", dispositivo="equipo-b", segundos=0)
    assert decidir_campo(actual, entrante) == DECISION_IGNORAR_ANTIGUA


def test_misma_operacion_no_se_repite():
    marca = _marca("valor", op_id="op-1")
    assert decidir_campo(marca, _marca("valor", op_id="op-1")) == DECISION_REPETIDA


def test_valor_identico_no_genera_ruido():
    actual = _marca("valor")
    entrante = _marca("valor", dispositivo="equipo-b", segundos=30)
    assert decidir_campo(actual, entrante) == DECISION_IGNORAR_IDENTICA


def test_empate_de_reloj_se_resuelve_por_dispositivo():
    """Sin relojes sincronizados, el desempate debe ser determinista"""
    actual = _marca("de-a", dispositivo="equipo-a")
    entrante = _marca("de-b", dispositivo="equipo-b")
    # "equipo-b" > "equipo-a", así que gana el remoto sin importar el orden
    assert decidir_campo(actual, entrante) == DECISION_APLICAR
    assert decidir_campo(entrante, actual) == DECISION_IGNORAR_ANTIGUA


# ----------------------------------------------------------------------
# Planificación por campos
# ----------------------------------------------------------------------
def test_campos_distintos_se_fusionan_sin_conflicto():
    actuales = {"cargo": _marca("Docente", op_id="op-1")}
    entrantes = {"telefono": _marca("555-0000", dispositivo="equipo-b", segundos=5)}
    plan = planificar_campos("empleados", "u-1", entrantes, actuales)
    assert plan.aplicar == {
        "telefono": _marca("555-0000", dispositivo="equipo-b", segundos=5).valor
    }
    assert plan.conflictos == ()


def test_choque_de_campo_conserva_el_valor_perdedor():
    actuales = {"telefono": _marca("111", op_id="op-local", segundos=30)}
    entrantes = {"telefono": _marca("222", dispositivo="equipo-b", segundos=10)}
    plan = planificar_campos("empleados", "u-1", entrantes, actuales)
    assert plan.aplicar == {}
    assert len(plan.conflictos) == 1
    conflicto = plan.conflictos[0]
    assert conflicto.ganador == GANADOR_LOCAL
    assert conflicto.valor_local == "111"
    assert conflicto.valor_remoto == "222"
    assert conflicto.fila_uuid == "u-1"


def test_campo_sensible_deja_conflicto_aunque_gane_el_remoto():
    """Un salario que cambia merece quedar auditado aunque la regla lo resuelva"""
    actuales = {"salario_base": _marca(1000.0, op_id="op-local")}
    entrantes = {"salario_base": _marca(1200.0, dispositivo="equipo-b", segundos=60)}
    plan = planificar_campos("empleados", "u-1", entrantes, actuales)
    assert plan.aplicar == {"salario_base": 1200.0}
    assert len(plan.conflictos) == 1
    conflicto = plan.conflictos[0]
    assert conflicto.ganador == GANADOR_REMOTO
    assert conflicto.regla.startswith(REGLA_CAMPO_SENSIBLE)


def test_plan_sin_cambios_cuando_todo_es_repetido():
    marca = _marca("valor", op_id="op-1")
    plan = planificar_campos("empleados", "u-1", {"cargo": marca}, {"cargo": marca})
    assert plan.sin_cambios
    assert plan.motivo is None or isinstance(plan.motivo, str)


# ----------------------------------------------------------------------
# Convergencia: mismo conjunto de operaciones, cualquier orden
# ----------------------------------------------------------------------
def test_convergencia_con_ediciones_en_campos_distintos():
    operaciones = [
        {"cargo": _marca("Director", dispositivo="equipo-a", segundos=0)},
        {"telefono": _marca("555-0001", dispositivo="equipo-b", segundos=5)},
    ]
    uno, otro = Nodo(), Nodo()
    for operacion in operaciones:
        uno.recibir("u-1", operacion)
    for operacion in reversed(operaciones):
        otro.recibir("u-1", operacion)
    assert uno.valores() == {"cargo": "Director", "telefono": "555-0001"}
    assert uno.valores() == otro.valores()


def test_convergencia_cuando_los_dos_equipos_tocan_lo_mismo():
    operaciones = [
        {"cargo": _marca("Docente", dispositivo="equipo-a", segundos=0)},
        {"cargo": _marca("Director", dispositivo="equipo-b", segundos=90)},
        {"cargo": _marca("Secretaria", dispositivo="equipo-c", segundos=30)},
    ]
    uno, otro = Nodo(), Nodo()
    for operacion in operaciones:
        uno.recibir("u-1", operacion)
    for operacion in reversed(operaciones):
        otro.recibir("u-1", operacion)
    assert uno.valores() == otro.valores() == {"cargo": "Director"}


def test_convergencia_con_empate_exacto_de_reloj():
    """Escrituras simultáneas: el desempate por dispositivo debe ser estable"""
    operaciones = [
        {"cargo": _marca("de-a", dispositivo="equipo-a", segundos=0)},
        {"cargo": _marca("de-b", dispositivo="equipo-b", segundos=0)},
        {"cargo": _marca("de-c", dispositivo="equipo-c", segundos=0)},
    ]
    resultados = set()
    for orden in (operaciones, list(reversed(operaciones))):
        nodo = Nodo()
        for operacion in orden:
            nodo.recibir("u-1", operacion)
        resultados.add(tuple(sorted(nodo.valores().items())))
    assert len(resultados) == 1
    assert resultados.pop()[0][1] == "de-c"


def test_convergencia_de_varios_registros():
    """La mezcla de filas distintas es independiente entre sí"""
    operaciones = [
        ("u-1", {"cargo": _marca("A", dispositivo="equipo-a", segundos=0)}),
        ("u-2", {"cargo": _marca("B", dispositivo="equipo-b", segundos=10)}),
        ("u-1", {"telefono": _marca("111", dispositivo="equipo-b", segundos=20)}),
    ]
    uno, otro = Nodo(), Nodo()
    for fila, campos in operaciones:
        uno.recibir(fila, campos)
    for fila, campos in reversed(operaciones):
        otro.recibir(fila, campos)
    assert uno.campos == otro.campos


# ----------------------------------------------------------------------
# Borrados
# ----------------------------------------------------------------------
def test_borrado_sobre_fila_desconocida_se_aplica():
    assert decidir_borrado(None, _marca(True)) == (BORRAR, None)


def test_borrado_posterior_a_la_actualizacion_gana():
    version = VersionFila(
        ultimo_op_id="op-1",
        actualizado_en=T0,
        dispositivo="equipo-a",
    )
    decision, conflicto = decidir_borrado_sobre_actualizacion(
        version, _marca(True, dispositivo="equipo-b", segundos=30, op_id="op-2")
    )
    assert decision == BORRAR
    assert conflicto is None


def test_borrado_antiguo_no_pisa_una_edicion_posterior():
    version = VersionFila(
        ultimo_op_id="op-1",
        actualizado_en=T0 + timedelta(seconds=60),
        dispositivo="equipo-a",
    )
    decision, conflicto = decidir_borrado_sobre_actualizacion(
        version, _marca(True, dispositivo="equipo-b", segundos=0, op_id="op-2")
    )
    assert decision == MANTENER_BORRADO
    assert conflicto is not None
    assert conflicto.ganador == GANADOR_LOCAL


def test_actualizacion_posterior_al_borrado_revive_la_fila():
    version = VersionFila(
        borrado=True,
        borrado_en=T0,
        borrado_op_id="op-borrado",
        borrado_dispositivo="equipo-a",
    )
    decision, conflicto = decidir_borrado(
        version, _marca("editado", dispositivo="equipo-b", segundos=120, op_id="op-nueva")
    )
    assert decision == REVIVIR
    assert conflicto is not None
    assert conflicto.regla == REGLA_REVIVE


def test_mismo_borrado_repetido_se_ignora():
    version = VersionFila(
        borrado=True,
        borrado_en=T0,
        borrado_op_id="op-borrado",
        borrado_dispositivo="equipo-a",
    )
    entrante = _marca(True, dispositivo="equipo-a", op_id="op-borrado")
    assert decidir_borrado(version, entrante) == (IGNORAR_BORRADO, None)


# ----------------------------------------------------------------------
# Valor idéntico con marca más reciente (defecto I.4)
# ----------------------------------------------------------------------
def test_valor_identico_mas_reciente_actualiza_la_marca():
    """
    El valor no cambia, pero el nodo debe recordar la escritura más reciente:
    si conserva la marca vieja, una operación intermedia fuera de orden se
    aplica sobre un valor que el emisor ya había reemplazado.
    """
    actual = _marca("valor", op_id="op-1", segundos=0)
    identico = _marca("valor", dispositivo="equipo-b", op_id="op-2", segundos=30)
    plan = planificar_campos("empleados", "u-1", {"cargo": identico}, {"cargo": actual})
    assert plan.aplicar == {}
    assert plan.sin_cambios
    assert plan.marcas == {"cargo": identico}


def test_convergencia_con_un_valor_identico_adelantado():
    """
    A tiene "X" en t0; el equipo B escribió "Y" en t10 y volvió a "X" en t20.
    Si la operación de t20 llega primero y la de t10 después, ambos órdenes
    deben terminar en "X" (antes el nodo que recibía primero t20 aplicaba Y).
    """
    t20 = _marca("X", dispositivo="equipo-b", op_id="b-20", segundos=20)
    t10 = _marca("Y", dispositivo="equipo-b", op_id="b-10", segundos=10)
    inicial = _marca("X", dispositivo="equipo-a", op_id="a-0", segundos=0)

    orden_normal = Nodo()
    orden_normal.campos["cargo"] = inicial
    orden_normal.recibir("u-1", {"cargo": t20})
    orden_normal.recibir("u-1", {"cargo": t10})

    orden_inverso = Nodo()
    orden_inverso.campos["cargo"] = inicial
    orden_inverso.recibir("u-1", {"cargo": t10})
    orden_inverso.recibir("u-1", {"cargo": t20})

    assert orden_normal.valores() == orden_inverso.valores() == {"cargo": "X"}
