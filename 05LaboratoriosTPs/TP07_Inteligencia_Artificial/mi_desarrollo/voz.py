"""Entrada local por voz para el mismo pipeline de texto del agente.

Las dependencias pesadas se importan solamente al usar ``--voz``. Ninguna clase
de este modulo conoce al robot ni puede ejecutar acciones fisicas.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import re
import unicodedata
from typing import Any, Callable, Protocol, Sequence

from configuracion import (
    CANALES_AUDIO,
    FRECUENCIA_AUDIO_HZ,
    STT_MODELO_CALIDAD,
    STT_MODELO_LIVIANO,
    directorio_modelos,
)
from emotes import resolver_emote


MENSAJE_RECHAZO_VOZ = "[VOZ NO CONFIRMADA] No ejecuto ninguna accion."
PROMPT_COMANDOS = (
    "Comandos en espanol rioplatense para un robot: avanza, retrocede, gira a "
    "la izquierda, gira a la derecha, detenete, saluda, estado de bateria, "
    "repeti, reversa, modo lento, modo normal, conta un chiste, baile, risa, "
    "brazos cruzados, pulgar arriba, apunta al cielo, pistolas, emote uno a "
    "seis, ayuda."
)


@dataclass(frozen=True)
class DispositivoAudio:
    indice: int
    nombre: str
    canales_entrada: int
    frecuencia_predeterminada: float


@dataclass(frozen=True)
class MetricasSTT:
    probabilidad_idioma: float | None = None
    logprob_promedio: float | None = None
    probabilidad_silencio: float | None = None


@dataclass(frozen=True)
class Transcripcion:
    texto: str
    texto_normalizado: str
    confianza_suficiente: bool
    motivo: str = ""
    metricas: MetricasSTT = MetricasSTT()


@dataclass(frozen=True)
class ConfiguracionCaptura:
    frecuencia_objetivo: int = FRECUENCIA_AUDIO_HZ
    canales: int = CANALES_AUDIO
    bloque_ms: int = 30
    calibracion_s: float = 1.0
    espera_inicio_s: float = 5.0
    duracion_max_s: float = 8.0
    silencio_final_s: float = 0.8
    voz_minima_s: float = 0.24
    prebuffer_s: float = 0.3
    multiplicador_ruido: float = 3.0
    rms_minimo: float = 0.008


@dataclass(frozen=True)
class PerfilSTT:
    nombre: str
    modelo: str
    beam_size: int


PERFILES_STT = {
    "quality": PerfilSTT("quality", STT_MODELO_CALIDAD, 5),
    "light": PerfilSTT("light", STT_MODELO_LIVIANO, 3),
}


class ErrorVoz(RuntimeError):
    pass


class SinHabla(ErrorVoz):
    pass


class ReconocedorVoz(Protocol):
    def listar_microfonos(self) -> Sequence[DispositivoAudio]: ...

    def escuchar(self, dispositivo: int | None = None) -> Transcripcion: ...


class DetectorEnergia:
    """Detector determinista de inicio/fin; recibe bloques RMS ya calculados."""

    def __init__(self, umbral: float, configuracion: ConfiguracionCaptura):
        self.umbral = umbral
        self.configuracion = configuracion
        self.inicio = False
        self.bloques_voz = 0
        self.bloques_silencio = 0
        self.bloques_habla_requeridos = max(
            1, round(configuracion.voz_minima_s * 1000 / configuracion.bloque_ms)
        )
        self.bloques_fin = max(
            1, round(configuracion.silencio_final_s * 1000 / configuracion.bloque_ms)
        )

    def alimentar(self, rms: float) -> tuple[bool, bool]:
        es_voz = rms >= self.umbral
        if es_voz:
            self.bloques_voz += 1
            self.bloques_silencio = 0
            if self.bloques_voz >= self.bloques_habla_requeridos:
                self.inicio = True
        elif self.inicio:
            self.bloques_silencio += 1
        else:
            self.bloques_voz = 0
        terminado = self.inicio and self.bloques_silencio >= self.bloques_fin
        return self.inicio, terminado


class CapturadorMicrofono:
    def __init__(self, configuracion: ConfiguracionCaptura | None = None):
        self.configuracion = configuracion or ConfiguracionCaptura()
        self._umbral_por_dispositivo: dict[int | None, float] = {}

    @staticmethod
    def _dependencias():
        try:
            import numpy as np
            import sounddevice as sd
        except ImportError as exc:
            raise ErrorVoz(
                "Faltan dependencias de voz. Instala requirements-voz.txt."
            ) from exc
        return np, sd

    def listar_microfonos(self) -> list[DispositivoAudio]:
        _, sd = self._dependencias()
        dispositivos = []
        try:
            inventario = sd.query_devices()
        except Exception as exc:
            raise ErrorVoz(f"no se pudieron consultar los microfonos: {exc}") from exc
        for indice, datos in enumerate(inventario):
            canales = int(datos.get("max_input_channels", 0))
            if canales > 0:
                dispositivos.append(
                    DispositivoAudio(
                        indice=indice,
                        nombre=str(datos.get("name", f"Dispositivo {indice}")),
                        canales_entrada=canales,
                        frecuencia_predeterminada=float(datos.get("default_samplerate", 0)),
                    )
                )
        return dispositivos

    def calibrar(self, dispositivo: int | None = None) -> float:
        np, sd = self._dependencias()
        frecuencia = self._frecuencia_compatible(sd, dispositivo)
        muestras = max(1, round(frecuencia * self.configuracion.calibracion_s))
        try:
            audio = sd.rec(
                muestras,
                samplerate=frecuencia,
                channels=self.configuracion.canales,
                dtype="float32",
                device=dispositivo,
                blocking=True,
            )
        except Exception as exc:
            raise ErrorVoz(f"no se pudo calibrar el microfono: {exc}") from exc
        rms_ruido = _rms(np, audio)
        umbral = max(
            self.configuracion.rms_minimo,
            rms_ruido * self.configuracion.multiplicador_ruido,
        )
        self._umbral_por_dispositivo[dispositivo] = umbral
        return umbral

    def capturar(self, dispositivo: int | None = None):
        np, sd = self._dependencias()
        frecuencia = self._frecuencia_compatible(sd, dispositivo)
        umbral = self._umbral_por_dispositivo.get(dispositivo)
        if umbral is None:
            umbral = self.calibrar(dispositivo)

        bloque = max(1, round(frecuencia * self.configuracion.bloque_ms / 1000))
        max_bloques = max(
            1, round(self.configuracion.duracion_max_s * 1000 / self.configuracion.bloque_ms)
        )
        espera_bloques = max(
            1, round(self.configuracion.espera_inicio_s * 1000 / self.configuracion.bloque_ms)
        )
        prebuffer = deque(
            maxlen=max(
                1, round(self.configuracion.prebuffer_s * 1000 / self.configuracion.bloque_ms)
            )
        )
        detector = DetectorEnergia(umbral, self.configuracion)
        audio_habla = []
        inicio_en = None

        try:
            with sd.InputStream(
                samplerate=frecuencia,
                channels=self.configuracion.canales,
                dtype="float32",
                blocksize=bloque,
                device=dispositivo,
            ) as stream:
                for numero_bloque in range(espera_bloques + max_bloques):
                    datos, overflow = stream.read(bloque)
                    if overflow:
                        raise ErrorVoz("overflow de audio: se descarta la orden completa")
                    copia = np.asarray(datos, dtype=np.float32).reshape(-1).copy()
                    estaba_iniciado = detector.inicio
                    iniciado, terminado = detector.alimentar(_rms(np, copia))
                    if not iniciado:
                        prebuffer.append(copia)
                        if numero_bloque >= espera_bloques:
                            raise SinHabla("no se detecto habla antes del timeout")
                        continue
                    if not estaba_iniciado:
                        audio_habla.extend(prebuffer)
                        prebuffer.clear()
                        inicio_en = numero_bloque
                    audio_habla.append(copia)
                    if terminado:
                        break
                    if inicio_en is not None and numero_bloque - inicio_en >= max_bloques:
                        break
        except (ErrorVoz, SinHabla):
            raise
        except Exception as exc:
            raise ErrorVoz(f"fallo la captura de audio: {exc}") from exc

        if not detector.inicio or detector.bloques_voz < detector.bloques_habla_requeridos:
            raise SinHabla("el fragmento de voz fue demasiado corto")
        audio = np.concatenate(audio_habla).astype(np.float32, copy=False)
        return _remuestrear(np, audio, frecuencia, self.configuracion.frecuencia_objetivo)

    def _frecuencia_compatible(self, sd, dispositivo: int | None) -> int:
        objetivo = self.configuracion.frecuencia_objetivo
        try:
            sd.check_input_settings(
                device=dispositivo,
                channels=self.configuracion.canales,
                dtype="float32",
                samplerate=objetivo,
            )
            return objetivo
        except Exception:
            datos = sd.query_devices(dispositivo, "input")
            frecuencia = int(round(float(datos["default_samplerate"])))
            if frecuencia <= 0:
                raise ErrorVoz("el microfono no informa una frecuencia compatible")
            return frecuencia


class TranscriptorFasterWhisper:
    def __init__(
        self,
        perfil: str = "quality",
        dispositivo: str = "cpu",
        modelo_factory: Callable[..., Any] | None = None,
    ):
        if perfil not in PERFILES_STT:
            raise ValueError(f"perfil STT invalido: {perfil}")
        if dispositivo not in ("cpu", "cuda"):
            raise ValueError("el dispositivo STT debe ser cpu o cuda")
        self.perfil = PERFILES_STT[perfil]
        self.dispositivo = dispositivo
        self._modelo_factory = modelo_factory
        self._modelo = None

    def _cargar_modelo(self):
        if self._modelo is not None:
            return self._modelo
        factory = self._modelo_factory
        if factory is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise ErrorVoz(
                    "No esta instalado faster-whisper. Instala requirements-voz.txt."
                ) from exc
            factory = WhisperModel
        ruta = directorio_modelos()
        ruta.mkdir(parents=True, exist_ok=True)
        try:
            self._modelo = factory(
                self.perfil.modelo,
                device=self.dispositivo,
                compute_type="int8" if self.dispositivo == "cpu" else "float16",
                download_root=str(ruta),
            )
        except Exception as exc:
            raise ErrorVoz(
                "no se pudo cargar el modelo STT; la primera instalacion requiere "
                f"Internet y espacio en {ruta}: {exc}"
            ) from exc
        return self._modelo

    def transcribir(self, audio) -> tuple[str, MetricasSTT]:
        modelo = self._cargar_modelo()
        try:
            segmentos_iter, info = modelo.transcribe(
                audio,
                language="es",
                beam_size=self.perfil.beam_size,
                temperature=0.0,
                condition_on_previous_text=False,
                initial_prompt=PROMPT_COMANDOS,
                vad_filter=True,
            )
            segmentos = list(segmentos_iter)
        except Exception as exc:
            raise ErrorVoz(f"fallo la transcripcion local: {exc}") from exc
        texto = " ".join(
            str(getattr(segmento, "text", "")).strip() for segmento in segmentos
        ).strip()
        logprobs = [
            float(s.avg_logprob) for s in segmentos
            if getattr(s, "avg_logprob", None) is not None
        ]
        silencios = [
            float(s.no_speech_prob) for s in segmentos
            if getattr(s, "no_speech_prob", None) is not None
        ]
        metricas = MetricasSTT(
            probabilidad_idioma=_opcional_float(getattr(info, "language_probability", None)),
            logprob_promedio=sum(logprobs) / len(logprobs) if logprobs else None,
            probabilidad_silencio=max(silencios) if silencios else None,
        )
        return texto, metricas


class ReconocedorVozLocal:
    def __init__(
        self,
        perfil: str = "quality",
        dispositivo_stt: str = "cpu",
        capturador: CapturadorMicrofono | None = None,
        transcriptor: TranscriptorFasterWhisper | None = None,
    ):
        self.capturador = capturador or CapturadorMicrofono()
        self.transcriptor = transcriptor or TranscriptorFasterWhisper(
            perfil, dispositivo_stt
        )

    def listar_microfonos(self) -> Sequence[DispositivoAudio]:
        return self.capturador.listar_microfonos()

    def calibrar(self, dispositivo: int | None = None) -> float:
        return self.capturador.calibrar(dispositivo)

    def escuchar(self, dispositivo: int | None = None) -> Transcripcion:
        audio = self.capturador.capturar(dispositivo)
        original, metricas = self.transcriptor.transcribir(audio)
        normalizado = normalizar_texto_voz(original)
        aceptado, motivo = evaluar_confianza(normalizado, metricas)
        return Transcripcion(original, normalizado, aceptado, motivo, metricas)


def normalizar_texto_voz(texto: str) -> str:
    """Normaliza despues de conservar el original; mantiene tildes informativas."""

    limpio = re.sub(r"\s+", " ", str(texto)).strip().lower()
    return limpio.strip(" \t\r\n.,;:!?¿¡")


def evaluar_confianza(texto: str, metricas: MetricasSTT) -> tuple[bool, str]:
    """Heuristica fail-closed: los scores de Whisper no son probabilidades calibradas."""

    if not texto:
        return False, "transcripcion vacia"
    if len(texto) > 160 or len(texto.split()) > 18:
        return False, "frase demasiado larga para un comando"
    if metricas.probabilidad_idioma is not None and metricas.probabilidad_idioma < 0.70:
        return False, "baja probabilidad de idioma espanol"
    if metricas.logprob_promedio is not None and metricas.logprob_promedio < -0.75:
        return False, "baja evidencia acustica"
    if metricas.probabilidad_silencio is not None and metricas.probabilidad_silencio > 0.35:
        return False, "alta probabilidad de silencio"
    if not _parece_orden_del_dominio(texto):
        return False, "la frase no coincide claramente con una intencion valida"
    return True, ""


def procesar_una_orden_por_voz(agente, reconocedor: ReconocedorVoz, dispositivo=None):
    """Unico puente voz->agente; incluso el rechazo atraviesa ``procesar``."""

    transcripcion = reconocedor.escuchar(dispositivo)
    if transcripcion.confianza_suficiente:
        resultado = agente.procesar(transcripcion.texto_normalizado)
    else:
        resultado = agente.procesar(
            f"[VOZ NO CONFIRMADA] {transcripcion.texto_normalizado}"
        )
        resultado["mensaje"] = MENSAJE_RECHAZO_VOZ + (
            f" Motivo: {transcripcion.motivo}" if transcripcion.motivo else ""
        )
    resultado["transcripcion_original"] = transcripcion.texto
    resultado["entrada"] = "voz"
    return resultado


def _parece_orden_del_dominio(texto: str) -> bool:
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    patrones = (
        r"\b(avanza|avanzar|muevete|mover|camina|caminar|anda|retrocede|retroceder)\b",
        r"\b(gira|girar|rota|media vuelta)\b",
        r"\b(detente|detenete|para|frena|quieto|no avances)\b",
        r"\b(saluda|saludo)\b",
        r"\b(bateria|estado)\b",
        r"\b(repeti|otra vez|de nuevo|hacelo de nuevo)\b",
        r"\b(reversa|deshace|reverti|volve atras)\b",
        r"\b(modo lento|mas despacio|modo normal|desactiva modo lento)\b",
        r"\b(chiste|contame algo gracioso|haceme reir)\b",
        r"\b(ayuda|help|comandos)\b",
    )
    return (
        resolver_emote(sin_tildes) is not None
        or any(re.search(patron, sin_tildes) for patron in patrones)
    )


def _rms(np, audio) -> float:
    valores = np.asarray(audio, dtype=np.float32).reshape(-1)
    if valores.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(valores), dtype=np.float64)))


def _remuestrear(np, audio, origen: int, destino: int):
    if origen == destino or len(audio) == 0:
        return audio
    cantidad = max(1, round(len(audio) * destino / origen))
    posiciones = np.linspace(0, len(audio) - 1, num=cantidad)
    return np.interp(posiciones, np.arange(len(audio)), audio).astype(np.float32)


def _opcional_float(valor):
    return None if valor is None else float(valor)
