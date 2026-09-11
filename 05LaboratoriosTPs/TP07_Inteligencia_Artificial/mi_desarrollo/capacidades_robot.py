"""Capacidades declaradas; nunca supone hardware ni metodos del SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class CapacidadesRobot:
    es_simulacion: bool
    variante_confirmada: bool = False
    manos_confirmadas: bool = False
    firmware_confirmado: bool = False
    sdk_confirmado: bool = False
    telemetria_bateria_confirmada: bool = False
    tts_nativo: bool = False
    audio_pcm_nativo: bool = False
    acciones_nativas: frozenset[str] = field(default_factory=frozenset)

    @property
    def hardware_confirmado(self) -> bool:
        return all(
            (
                self.variante_confirmada,
                self.manos_confirmadas,
                self.firmware_confirmado,
                self.sdk_confirmado,
            )
        )

    def permite_emote_fisico(self, accion_nativa: str | None = None) -> bool:
        if self.es_simulacion:
            return True
        if not self.hardware_confirmado or not self.telemetria_bateria_confirmada:
            return False
        return accion_nativa is not None and accion_nativa in self.acciones_nativas


def capacidades_simulador() -> CapacidadesRobot:
    return CapacidadesRobot(es_simulacion=True)


def capacidades_hardware_desconocido() -> CapacidadesRobot:
    return CapacidadesRobot(es_simulacion=False)


def detectar_capacidades(
    robot=None,
    datos_confirmados: Mapping[str, Any] | None = None,
    arm_client=None,
) -> CapacidadesRobot:
    """Detecta lo comprobable y deja en falso todo lo que no este confirmado.

    ``datos_confirmados`` debe provenir del inventario real del robot; no se
    completan valores por modelo supuesto. Las acciones se consultan al cliente
    oficial en runtime y nunca se hardcodean identificadores numericos.
    """

    if robot is None or getattr(robot, "destino", None) == "simulador":
        return capacidades_simulador()
    datos = dict(datos_confirmados or {})
    acciones = _consultar_acciones(arm_client) if arm_client is not None else frozenset()
    return CapacidadesRobot(
        es_simulacion=False,
        variante_confirmada=bool(datos.get("variante_confirmada", False)),
        manos_confirmadas=bool(datos.get("manos_confirmadas", False)),
        firmware_confirmado=bool(datos.get("firmware_confirmado", False)),
        sdk_confirmado=bool(datos.get("sdk_confirmado", False)),
        telemetria_bateria_confirmada=bool(
            datos.get("telemetria_bateria_confirmada", False)
        ),
        tts_nativo=bool(datos.get("tts_nativo", False)),
        audio_pcm_nativo=bool(datos.get("audio_pcm_nativo", False)),
        acciones_nativas=acciones,
    )


def _consultar_acciones(arm_client) -> frozenset[str]:
    consultar = getattr(arm_client, "GetActionList", None)
    if not callable(consultar):
        return frozenset()
    try:
        respuesta = consultar()
    except Exception:
        return frozenset()
    if isinstance(respuesta, tuple) and len(respuesta) >= 2:
        codigo, datos = respuesta[0], respuesta[1]
        if codigo not in (None, 0):
            return frozenset()
    else:
        datos = respuesta
    if isinstance(datos, Mapping):
        candidatos = list(datos.keys()) + list(datos.values())
    elif isinstance(datos, (list, tuple, set, frozenset)):
        candidatos = list(datos)
    else:
        return frozenset()
    return frozenset(
        str(candidato).strip().lower()
        for candidato in candidatos
        if isinstance(candidato, str) and candidato.strip()
    )
