import tempfile
import unittest
from unittest.mock import patch

from voz import TranscriptorFasterWhisper


class Segmento:
    text = " Avanza medio metro. "
    avg_logprob = -0.2
    no_speech_prob = 0.05


class Info:
    language_probability = 0.98


class ModeloFalso:
    def transcribe(self, audio, **opciones):
        self.opciones = opciones
        return iter([Segmento()]), Info()


class TranscripcionTests(unittest.TestCase):
    def test_configura_espanol_y_recoge_metricas(self):
        modelo = ModeloFalso()
        with tempfile.TemporaryDirectory() as ruta, patch.dict(
            "os.environ", {"TP07_MODEL_DIR": ruta}, clear=False
        ):
            transcriptor = TranscriptorFasterWhisper(
                "quality", modelo_factory=lambda *args, **kwargs: modelo,
            )
            texto, metricas = transcriptor.transcribir([0.0])
        self.assertEqual("Avanza medio metro.", texto)
        self.assertEqual("es", modelo.opciones["language"])
        self.assertFalse(modelo.opciones["condition_on_previous_text"])
        self.assertAlmostEqual(0.98, metricas.probabilidad_idioma)


if __name__ == "__main__":
    unittest.main()

