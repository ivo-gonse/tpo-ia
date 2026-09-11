import unittest

from mi_tp07 import AgenteRobot
from voz import MetricasSTT, Transcripcion, procesar_una_orden_por_voz


class STTFalso:
    def __init__(self, transcripcion):
        self.transcripcion = transcripcion

    def escuchar(self, dispositivo=None):
        return self.transcripcion


class IntegracionVozTests(unittest.TestCase):
    def test_voz_confirmada_usa_el_mismo_procesar(self):
        agente = AgenteRobot()
        stt = STTFalso(Transcripcion("Avanzá 1 metro", "avanzá 1 metro", True))
        r = procesar_una_orden_por_voz(agente, stt)
        self.assertTrue(r["ejecutar"])
        self.assertEqual("MOVER", r["tipo"])
        self.assertEqual("voz", r["entrada"])

    def test_voz_no_confirmada_es_bloqueada_por_el_validador(self):
        agente = AgenteRobot()
        stt = STTFalso(
            Transcripcion(
                "Avanza", "avanza", False, "baja evidencia",
                MetricasSTT(0.9, -1.1, 0.1),
            )
        )
        r = procesar_una_orden_por_voz(agente, stt)
        self.assertFalse(r["ejecutar"])
        self.assertTrue(r["bloqueado"])
        self.assertIn("VOZ NO CONFIRMADA", r["mensaje"])


if __name__ == "__main__":
    unittest.main()

