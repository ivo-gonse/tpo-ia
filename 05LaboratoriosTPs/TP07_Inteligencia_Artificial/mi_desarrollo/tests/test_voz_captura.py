import unittest

from voz import ConfiguracionCaptura, DetectorEnergia


class CapturaTests(unittest.TestCase):
    def test_detector_exige_habla_sostenida_y_finaliza_por_silencio(self):
        config = ConfiguracionCaptura(
            bloque_ms=100, voz_minima_s=0.2, silencio_final_s=0.3,
        )
        detector = DetectorEnergia(umbral=0.1, configuracion=config)
        self.assertEqual((False, False), detector.alimentar(0.01))
        self.assertEqual((False, False), detector.alimentar(0.2))
        self.assertEqual((True, False), detector.alimentar(0.2))
        self.assertEqual((True, False), detector.alimentar(0.01))
        self.assertEqual((True, False), detector.alimentar(0.01))
        self.assertEqual((True, True), detector.alimentar(0.01))


if __name__ == "__main__":
    unittest.main()

