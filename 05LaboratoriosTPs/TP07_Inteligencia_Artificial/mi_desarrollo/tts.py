"""Adaptadores de TTS con degradacion segura a consola."""

from __future__ import annotations

from typing import Callable, Protocol

from capacidades_robot import CapacidadesRobot


class ErrorTTS(RuntimeError):
    pass


class SintetizadorVoz(Protocol):
    def hablar(self, texto: str) -> bool: ...

    def detener(self) -> None: ...


class TTSConsola:
    def __init__(self, salida: Callable[[str], None] = print):
        self.salida = salida

    def hablar(self, texto: str) -> bool:
        self.salida(f"[ROBOT] {texto}")
        return True

    def detener(self) -> None:
        return None


class TTSLocalPyttsx3:
    """TTS offline mediante las voces instaladas en el sistema operativo."""

    def __init__(self):
        self._motor = None

    def _inicializar(self):
        if self._motor is not None:
            return self._motor
        try:
            import pyttsx3
        except ImportError as exc:
            raise ErrorTTS("pyttsx3 no esta instalado") from exc
        try:
            motor = pyttsx3.init()
            for voz in motor.getProperty("voices") or []:
                descripcion = " ".join(
                    [str(getattr(voz, "name", "")), str(getattr(voz, "id", ""))]
                    + [str(x) for x in (getattr(voz, "languages", None) or [])]
                ).lower()
                if any(marca in descripcion for marca in ("spanish", "español", "es_", "es-")):
                    motor.setProperty("voice", voz.id)
                    break
            self._motor = motor
            return motor
        except Exception as exc:
            raise ErrorTTS(f"no se pudo inicializar el TTS local: {exc}") from exc

    def hablar(self, texto: str) -> bool:
        try:
            motor = self._inicializar()
            motor.say(texto)
            motor.runAndWait()
            return True
        except ErrorTTS:
            raise
        except Exception as exc:
            raise ErrorTTS(f"fallo el TTS local: {exc}") from exc

    def detener(self) -> None:
        if self._motor is not None:
            self._motor.stop()


class TTSUnitreeConfirmado:
    """Usa ``AudioClient.TtsMaker`` oficial solo con capacidad confirmada.

    El cliente se inyecta: este modulo no supone version del SDK, interfaz de red
    ni identificadores. El ``speaker_id`` tambien debe provenir de configuracion
    verificada para el robot concreto.
    """

    def __init__(
        self,
        audio_client,
        capacidades: CapacidadesRobot,
        speaker_id: int,
    ):
        if not capacidades.hardware_confirmado or not capacidades.tts_nativo:
            raise ErrorTTS("el TTS nativo del G1 no esta confirmado")
        if not callable(getattr(audio_client, "TtsMaker", None)):
            raise ErrorTTS("el cliente verificado no expone AudioClient.TtsMaker")
        self.audio_client = audio_client
        self.speaker_id = int(speaker_id)

    def hablar(self, texto: str) -> bool:
        try:
            respuesta = self.audio_client.TtsMaker(texto, self.speaker_id)
        except Exception as exc:
            raise ErrorTTS(f"fallo el TTS nativo confirmado: {exc}") from exc
        # El SDK puede devolver codigo o tupla segun version; solo 0 confirma exito.
        codigo = respuesta[0] if isinstance(respuesta, tuple) and respuesta else respuesta
        if codigo not in (None, 0):
            raise ErrorTTS(f"el TTS nativo devolvio codigo {codigo}")
        return True

    def detener(self) -> None:
        detener = getattr(self.audio_client, "PlayStop", None)
        if callable(detener):
            detener()


class TTSConFallback:
    def __init__(self, principal: SintetizadorVoz, fallback: SintetizadorVoz):
        self.principal = principal
        self.fallback = fallback
        self.ultimo_error: str | None = None

    def hablar(self, texto: str) -> bool:
        try:
            if self.principal.hablar(texto):
                self.ultimo_error = None
                return True
        except Exception as exc:
            self.ultimo_error = str(exc)
        return bool(self.fallback.hablar(texto))

    def detener(self) -> None:
        for sintetizador in (self.principal, self.fallback):
            try:
                sintetizador.detener()
            except Exception:
                pass


def crear_tts(
    capacidades: CapacidadesRobot,
    usar_local: bool = False,
    audio_client=None,
    speaker_id: int | None = None,
    salida: Callable[[str], None] = print,
) -> SintetizadorVoz:
    consola = TTSConsola(salida)
    if (
        audio_client is not None
        and speaker_id is not None
        and capacidades.hardware_confirmado
        and capacidades.tts_nativo
    ):
        return TTSConFallback(
            TTSUnitreeConfirmado(audio_client, capacidades, speaker_id), consola
        )
    if usar_local:
        return TTSConFallback(TTSLocalPyttsx3(), consola)
    return consola

