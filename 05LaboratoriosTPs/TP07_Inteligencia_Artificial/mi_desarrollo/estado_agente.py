"""Estado explicito del agente, independiente del robot y de la interfaz."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class AccionUsuario:
    tipo: str
    parametros: dict[str, Any]
    texto_original: str

    def copia(self) -> "AccionUsuario":
        return AccionUsuario(self.tipo, dict(self.parametros), self.texto_original)


@dataclass
class EstadoAgente:
    modo_lento: bool = False
    historial: list[dict[str, Any]] = field(default_factory=list)
    ultima_accion_ejecutada: Optional[AccionUsuario] = None
    ultimo_movimiento_reversible: Optional[AccionUsuario] = None
    emote_activo: Optional[str] = None
    tts_activo: bool = False

    def registrar_resultado(self, resultado: dict[str, Any]) -> None:
        copia = dict(resultado)
        copia["parametros"] = dict(resultado.get("parametros", {}))
        self.historial.append(copia)

    def registrar_ejecucion(self, accion: AccionUsuario) -> None:
        copia = accion.copia()
        self.ultima_accion_ejecutada = copia
        if copia.tipo in ("MOVER", "GIRAR"):
            self.ultimo_movimiento_reversible = copia


def invertir_movimiento(accion: AccionUsuario) -> AccionUsuario:
    """Invierte un movimiento de forma aproximada, sin prometer navegacion exacta."""

    parametros = dict(accion.parametros)
    if accion.tipo == "MOVER":
        parametros["direccion"] = (
            "adelante" if parametros.get("direccion") == "atras" else "atras"
        )
    elif accion.tipo == "GIRAR":
        parametros["direccion"] = (
            "izquierda" if parametros.get("direccion") == "derecha" else "derecha"
        )
    else:
        raise ValueError("solo MOVER y GIRAR tienen una reversa definida")
    return AccionUsuario(accion.tipo, parametros, "reversa aproximada")
