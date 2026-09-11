import unittest

from estado_agente import AccionUsuario, EstadoAgente, invertir_movimiento


class EstadoAgenteTests(unittest.TestCase):
    def test_registra_ultima_accion_y_movimiento(self):
        estado = EstadoAgente()
        accion = AccionUsuario("MOVER", {"direccion": "adelante"}, "avanza")
        estado.registrar_ejecucion(accion)
        self.assertEqual("MOVER", estado.ultima_accion_ejecutada.tipo)
        self.assertEqual("MOVER", estado.ultimo_movimiento_reversible.tipo)

    def test_reversa_de_movimiento_no_muta_el_original(self):
        original = AccionUsuario("MOVER", {"direccion": "adelante", "distancia_m": 1}, "avanza")
        reversa = invertir_movimiento(original)
        self.assertEqual("atras", reversa.parametros["direccion"])
        self.assertEqual("adelante", original.parametros["direccion"])

    def test_reversa_de_giro(self):
        original = AccionUsuario("GIRAR", {"direccion": "derecha", "angulo_deg": 90}, "gira")
        self.assertEqual("izquierda", invertir_movimiento(original).parametros["direccion"])

    def test_no_inventa_reversa_para_otras_acciones(self):
        with self.assertRaises(ValueError):
            invertir_movimiento(AccionUsuario("SALUDO", {}, "hola"))


if __name__ == "__main__":
    unittest.main()

