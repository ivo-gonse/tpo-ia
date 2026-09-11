import unittest

from evaluar import cargar_casos, evaluar
from mi_tp07 import AgenteRobot


class CasosOriginalesTests(unittest.TestCase):
    def test_los_25_casos_originales(self):
        resumen = evaluar(AgenteRobot(), mostrar=False)
        self.assertEqual(25, resumen["casos"])
        self.assertEqual(25, resumen["aciertos"])
        self.assertEqual(
            resumen["peligrosos_totales"],
            resumen["peligrosos_bloqueados"],
        )

    def test_las_25_intenciones_originales_tambien_coinciden(self):
        agente = AgenteRobot()
        for caso in cargar_casos():
            with self.subTest(caso=caso["id"]):
                respuesta = agente.procesar(caso["texto"])
                self.assertEqual(caso["intencion_esperada"], respuesta["tipo"])


if __name__ == "__main__":
    unittest.main()
