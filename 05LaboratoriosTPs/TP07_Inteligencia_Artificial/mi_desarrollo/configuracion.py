"""Configuracion portable y segura para recursos locales del TP07."""

from __future__ import annotations

import os
from pathlib import Path


def directorio_modelos() -> Path:
    """Devuelve la ubicacion externa al repo para modelos descargados.

    La funcion no crea carpetas ni descarga archivos. Eso queda a cargo del comando
    explicito de instalacion para evitar escrituras y red inesperadas al importar.
    """

    configurado = os.environ.get("TP07_MODEL_DIR")
    if configurado:
        return _validar_directorio_externo(Path(configurado).expanduser().resolve())

    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_CACHE_HOME")
    if base:
        return _validar_directorio_externo(
            (Path(base) / "uade-robot-lab" / "tp07" / "modelos").resolve()
        )
    return _validar_directorio_externo(
        (Path.home() / ".cache" / "uade-robot-lab" / "tp07" / "modelos").resolve()
    )


def _validar_directorio_externo(ruta: Path) -> Path:
    raiz_tp = Path(__file__).resolve().parent.parent
    if ruta == raiz_tp or raiz_tp in ruta.parents:
        raise ValueError(
            "TP07_MODEL_DIR debe estar fuera del repositorio para no versionar modelos"
        )
    return ruta


STT_BACKEND_PREDETERMINADO = "faster-whisper"
STT_MODELO_CALIDAD = "large-v3"
STT_MODELO_LIVIANO = "small"
STT_DISPOSITIVO_PREDETERMINADO = "cpu"
FRECUENCIA_AUDIO_HZ = 16_000
CANALES_AUDIO = 1
