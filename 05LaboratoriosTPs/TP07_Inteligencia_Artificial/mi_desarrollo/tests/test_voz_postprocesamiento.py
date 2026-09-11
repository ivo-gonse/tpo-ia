import unittest

from voz import MetricasSTT, evaluar_confianza, normalizar_texto_voz


class PostprocesamientoTests(unittest.TestCase):
    def test_conserva_original_fuera_de_la_normalizacion(self):
        original = "  ¡GIRÁ   a la Derecha! "
        self.assertEqual("girá a la derecha", normalizar_texto_voz(original))
        self.assertEqual("  ¡GIRÁ   a la Derecha! ", original)

    def test_acepta_orden_clara_con_metricas_buenas(self):
        ok, _ = evaluar_confianza(
            "avanza medio metro", MetricasSTT(0.99, -0.2, 0.02),
        )
        self.assertTrue(ok)

    def test_rechaza_baja_evidencia_aunque_parezca_movimiento(self):
        ok, motivo = evaluar_confianza(
            "avanza medio metro", MetricasSTT(0.99, -1.2, 0.02),
        )
        self.assertFalse(ok)
        self.assertIn("acustica", motivo)

    def test_no_convierte_charla_ambigua_en_comando(self):
        ok, _ = evaluar_confianza(
            "me parece que tal vez", MetricasSTT(0.99, -0.1, 0.01),
        )
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()

