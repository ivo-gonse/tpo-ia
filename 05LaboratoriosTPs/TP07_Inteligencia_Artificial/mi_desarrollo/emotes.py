"""Emotes semanticos, separados de cualquier posicion articular."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import random
import re
import unicodedata
from typing import Callable

from capacidades_robot import CapacidadesRobot


class ImplementacionEmote(str, Enum):
    NATIVE = "native"
    CUSTOM_POSE = "custom_pose"
    SIMULATED_ONLY = "simulated_only"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class EspecificacionEmote:
    nombre: str
    implementacion: ImplementacionEmote
    accion_nativa: str | None = None
    requiere_manos_diestras: bool = False
    texto_tts: str | None = None
    pendiente_para_real: str = ""


CATALOGO_EMOTES: tuple[EspecificacionEmote, ...] = (
    EspecificacionEmote(
        "RISA", ImplementacionEmote.SIMULATED_ONLY,
        pendiente_para_real="falta una accion oficial equivalente confirmada en el firmware",
    ),
    EspecificacionEmote(
        "BAILE", ImplementacionEmote.SIMULATED_ONLY,
        pendiente_para_real="no hay una accion segura aprobada en el catalogo actual",
    ),
    EspecificacionEmote(
        "BRAZOS_CRUZADOS_COSTADO", ImplementacionEmote.CUSTOM_POSE,
        pendiente_para_real=(
            "faltan limites, pose oficial y validacion de colision del G1 exacto"
        ),
    ),
    EspecificacionEmote(
        "PULGAR_ARRIBA", ImplementacionEmote.CUSTOM_POSE,
        requiere_manos_diestras=True,
        pendiente_para_real="falta confirmar el tipo y control de las manos instaladas",
    ),
    EspecificacionEmote(
        "APUNTAR_CIELO_DOS_BRAZOS", ImplementacionEmote.NATIVE,
        accion_nativa="hands up",
        pendiente_para_real=(
            "falta confirmar hardware, firmware, SDK y que hands up figure en runtime"
        ),
    ),
    EspecificacionEmote(
        "FINGER_GUNS_BANG_BANG", ImplementacionEmote.CUSTOM_POSE,
        requiere_manos_diestras=True,
        texto_tts="bang bang",
        pendiente_para_real=(
            "faltan manos diestras confirmadas y una pose oficial segura"
        ),
    ),
)

EMOTES_POR_NUMERO = {
    "1": "RISA",
    "2": "BAILE",
    "3": "BRAZOS_CRUZADOS_COSTADO",
    "4": "PULGAR_ARRIBA",
    "5": "APUNTAR_CIELO_DOS_BRAZOS",
    "6": "FINGER_GUNS_BANG_BANG",
}
_NUMEROS_EMOTE = {
    "uno": "1",
    "dos": "2",
    "tres": "3",
    "cuatro": "4",
    "cinco": "5",
    "seis": "6",
}


def resolver_emote(texto: str) -> str | None:
    """Traduce una mención humana a un nombre semántico del catálogo.

    Esta función no sabe nada de MuJoCo. Admite frases completas para que se
    pueda reutilizar tanto en órdenes directas como en ``chiste + emote``.
    """

    normalizado = _normalizar_texto(texto)
    numero = re.search(
        r"\bemote(?:\s+numero)?\s+(1|2|3|4|5|6|uno|dos|tres|cuatro|cinco|seis)\b",
        normalizado,
    )
    if numero:
        valor = _NUMEROS_EMOTE.get(numero.group(1), numero.group(1))
        return EMOTES_POR_NUMERO[valor]

    patrones = (
        ("FINGER_GUNS_BANG_BANG", (
            r"\bfinger\s+guns?\b",
            r"\bbang\s+bang\b",
            r"\bpistolas?\b",
            r"\bdispara\s+con\s+las\s+manos\b",
        )),
        ("APUNTAR_CIELO_DOS_BRAZOS", (
            r"\bapunta\s+al\s+cielo\b",
            r"\bbrazos?\s+arriba\b",
            r"\bsenala\s+arriba\b",
            r"\bapunta\s+arriba\s+con\s+los\s+dos\s+brazos\b",
        )),
        ("BRAZOS_CRUZADOS_COSTADO", (
            r"\bbrazos?\s+cruzados?\b",
            r"\bcruzate\s+de\s+brazos\b",
            r"\bhacete\s+el\s+canchero\b",
            r"\bponete\s+de\s+costado\b",
        )),
        ("PULGAR_ARRIBA", (
            r"\bpulgar\s+arriba\b",
            r"\bhace\s+(?:un\s+)?like\b",
            r"\blike\b",
            r"\baprobado\b",
        )),
        ("BAILE", (
            r"\bbaile\b",
            r"\bbaila\b",
            r"\bponete\s+a\s+bailar\b",
        )),
        ("RISA", (
            r"\brisa\b",
            r"\breite\b",
            r"\bhace\s+el\s+de\s+la\s+risa\b",
        )),
    )
    for nombre, expresiones in patrones:
        if any(re.search(expresion, normalizado) for expresion in expresiones):
            return nombre
    return None


def _normalizar_texto(texto: str) -> str:
    minusculas = "" if texto is None else str(texto).lower()
    return "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", minusculas)
        if unicodedata.category(caracter) != "Mn"
    )


class ErrorEmote(RuntimeError):
    pass


class BackendEmotesSimulador:
    def __init__(
        self,
        salida: Callable[[str], None] = print,
        simulador=None,
        habilitado: bool = True,
    ):
        self.salida = salida
        self.simulador = simulador
        self.habilitado = bool(habilitado)

    def puede_ejecutar(self, _emote: EspecificacionEmote) -> bool:
        return self.habilitado

    def ejecutar(self, emote: EspecificacionEmote) -> None:
        if not self.habilitado:
            raise ErrorEmote("el simulador conectado no admite emotes del G1")
        self.salida(f"[EMOTE] {emote.nombre}")
        if self.simulador is not None:
            self.simulador.ejecutar_emote(emote.nombre)

    def cancelar(self) -> None:
        if self.simulador is not None:
            self.simulador.cancelar()
        self.salida("[EMOTE] CANCELADO")


class BackendEmotesRealConfirmado:
    """Traduce solo acciones nativas verificadas mediante el cliente oficial.

    Las poses custom permanecen deliberadamente sin implementacion real.
    """

    ACCION_NEUTRAL = "release arm"

    def __init__(self, robot, arm_client, capacidades: CapacidadesRobot):
        if capacidades.es_simulacion or not capacidades.hardware_confirmado:
            raise ErrorEmote("el hardware real no esta completamente confirmado")
        if not capacidades.telemetria_bateria_confirmada:
            raise ErrorEmote("la telemetria de bateria real no esta confirmada")
        self.robot = robot
        self.arm_client = arm_client
        self.capacidades = capacidades

    def puede_ejecutar(self, emote: EspecificacionEmote) -> bool:
        return (
            emote.implementacion == ImplementacionEmote.NATIVE
            and emote.accion_nativa is not None
            and emote.accion_nativa in self.capacidades.acciones_nativas
            and self.ACCION_NEUTRAL in self.capacidades.acciones_nativas
            and callable(getattr(self.arm_client, "ExecuteActionByName", None))
        )

    def ejecutar(self, emote: EspecificacionEmote) -> None:
        if not self.puede_ejecutar(emote):
            raise ErrorEmote(f"{emote.nombre} no esta habilitado para este hardware")
        self.robot.detenerse()
        self._verificar_estado_y_bateria()
        try:
            respuesta = self.arm_client.ExecuteActionByName(emote.accion_nativa)
            self._verificar_codigo(respuesta, emote.accion_nativa)
        finally:
            self._volver_a_neutral()

    def cancelar(self) -> None:
        # No se asume thread-safety: este hook se usa en limites entre comandos.
        errores = []
        try:
            self.robot.detenerse()
        except Exception as exc:
            errores.append(f"stop: {exc}")
        try:
            detener_custom = getattr(self.arm_client, "StopCustomAction", None)
            if callable(detener_custom):
                detener_custom()
        except Exception as exc:
            errores.append(f"StopCustomAction: {exc}")
        try:
            self._volver_a_neutral()
        except Exception as exc:
            errores.append(f"neutral: {exc}")
        if errores:
            raise ErrorEmote("; ".join(errores))

    def _verificar_estado_y_bateria(self) -> None:
        estado = self.robot.verificar_estado()
        bateria = estado.get("bateria") if isinstance(estado, dict) else getattr(
            estado, "bateria", None
        )
        if bateria is None:
            raise ErrorEmote("bateria desconocida: el emote real queda bloqueado")
        minimo = getattr(self.robot.perfil, "bateria_min", 25)
        if int(bateria) < int(minimo):
            raise ErrorEmote(f"bateria {bateria}% menor al minimo {minimo}%")

    def _volver_a_neutral(self) -> None:
        if self.ACCION_NEUTRAL not in self.capacidades.acciones_nativas:
            return
        ejecutar = getattr(self.arm_client, "ExecuteActionByName", None)
        if callable(ejecutar):
            respuesta = ejecutar(self.ACCION_NEUTRAL)
            self._verificar_codigo(respuesta, self.ACCION_NEUTRAL)

    @staticmethod
    def _verificar_codigo(respuesta, accion: str) -> None:
        codigo = respuesta[0] if isinstance(respuesta, tuple) and respuesta else respuesta
        if codigo not in (None, 0):
            raise ErrorEmote(f"la accion {accion} devolvio codigo {codigo}")


class EmoteManager:
    def __init__(
        self,
        capacidades: CapacidadesRobot,
        backend,
        rng: random.Random | None = None,
        hablar: Callable[[str], object] | None = None,
        salida: Callable[[str], None] = print,
    ):
        self.capacidades = capacidades
        self.backend = backend
        # Seed estable por defecto: evita que una prueba de TTS cambie de
        # resultado solo porque el primer emote al azar fue FINGER_GUNS (el
        # unico que agrega "bang bang"). Quien necesite otra secuencia puede
        # seguir inyectando cualquier Random.
        self.rng = rng or random.Random(0)
        self.hablar = hablar
        self.salida = salida
        self.ultimo_emote: str | None = None
        self.activo: str | None = None

    def disponibles(self) -> list[EspecificacionEmote]:
        if self.capacidades.es_simulacion:
            puede = getattr(self.backend, "puede_ejecutar", lambda _emote: True)
            return [emote for emote in CATALOGO_EMOTES if puede(emote)]
        puede = getattr(self.backend, "puede_ejecutar", lambda _emote: False)
        return [emote for emote in CATALOGO_EMOTES if puede(emote)]

    def ejecutar_aleatorio(self, _chiste: str | None = None) -> str | None:
        disponibles = self.disponibles()
        if not disponibles:
            self.salida("[EMOTE] ninguno habilitado para el hardware actual")
            return None
        candidatos = [e for e in disponibles if e.nombre != self.ultimo_emote]
        if not candidatos:
            candidatos = disponibles
        elegido = self.rng.choice(candidatos)
        return elegido.nombre if self.ejecutar(elegido.nombre) else None

    def ejecutar(self, nombre: str) -> bool:
        emote = _buscar_emote(nombre)
        if emote not in self.disponibles():
            self.salida(f"[EMOTE] {emote.nombre} no disponible")
            return False
        self.activo = emote.nombre
        try:
            self.backend.ejecutar(emote)
            if emote.texto_tts and self.hablar is not None:
                try:
                    self.hablar(emote.texto_tts)
                except Exception:
                    pass
            self.ultimo_emote = emote.nombre
            return True
        except Exception as exc:
            self.salida(f"[EMOTE] {emote.nombre} ERROR: {exc}")
            return False
        finally:
            self.activo = None

    def cancelar(self) -> None:
        try:
            self.backend.cancelar()
        except Exception as exc:
            self.salida(f"[EMOTE] error al cancelar: {exc}")
        finally:
            self.activo = None


def crear_emote_manager(
    capacidades: CapacidadesRobot,
    robot=None,
    arm_client=None,
    rng: random.Random | None = None,
    hablar: Callable[[str], object] | None = None,
    salida: Callable[[str], None] = print,
) -> EmoteManager:
    if capacidades.es_simulacion:
        simulador = None
        habilitado = True
        if robot is not None:
            try:
                from simulador_emotes import SimuladorEmotes

                simulador = SimuladorEmotes(robot)
            except (ValueError, RuntimeError):
                # Un Go2 o un transporte DDS no se presenta como si pudiera
                # mover el G1. El modo sin robot conserva el backend semantico
                # para tests del catalogo.
                habilitado = False
        backend = BackendEmotesSimulador(
            salida, simulador=simulador, habilitado=habilitado
        )
    elif arm_client is not None and capacidades.hardware_confirmado:
        backend = BackendEmotesRealConfirmado(robot, arm_client, capacidades)
    else:
        # Un backend de log mantiene la API viva, pero ``disponibles`` sera vacio.
        backend = BackendEmotesSimulador(salida, habilitado=False)
    return EmoteManager(capacidades, backend, rng, hablar, salida)


def _buscar_emote(nombre: str) -> EspecificacionEmote:
    buscado = str(nombre).strip().upper()
    for emote in CATALOGO_EMOTES:
        if emote.nombre == buscado:
            return emote
    raise ErrorEmote(f"emote desconocido: {nombre}")
