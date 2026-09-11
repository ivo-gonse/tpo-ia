import unittest

from estado_agente import AccionUsuario
from mi_tp07 import AgenteRobot


class PerfilFalso:
    nombre = "prueba"
    velocidad_max = 0.2
    velocidad_angular_max = 0.5
    duracion_max = 5.0
    bateria_min = 25


class RobotFalso:
    def __init__(self):
        self.perfil = PerfilFalso()
        self.llamadas = []

    def avanzar(self, velocidad, tiempo):
        self.llamadas.append(("avanzar", velocidad, tiempo))

    def girar(self, velocidad, tiempo):
        self.llamadas.append(("girar", velocidad, tiempo))

    def detenerse(self):
        self.llamadas.append(("detenerse",))

    def saludar(self):
        self.llamadas.append(("saludar",))

    def verificar_estado(self):
        self.llamadas.append(("estado",))
        return {"bateria": 100}


class MemoriaYModosTests(unittest.TestCase):
    def setUp(self):
        self.robot = RobotFalso()
        self.agente = AgenteRobot(self.robot)

    def test_repetir_sin_historial(self):
        r = self.agente.procesar("repeti")
        self.assertFalse(r["ejecutar"])
        self.assertIn("no hay", r["mensaje"])

    def test_repetir_mover(self):
        self.agente.procesar("avanza 0.1 metros")
        self.robot.llamadas.clear()
        r = self.agente.procesar("otra vez")
        self.assertTrue(r["ejecutar"])
        self.assertEqual("MOVER", r["tipo"])
        self.assertEqual("avanzar", self.robot.llamadas[-1][0])

    def test_repetir_giro(self):
        self.agente.procesar("gira 20 grados a la derecha")
        r = self.agente.procesar("hacelo de nuevo")
        self.assertTrue(r["ejecutar"])
        self.assertEqual("GIRAR", r["tipo"])

    def test_repetir_no_reemplaza_la_ultima_accion_con_el_meta_comando(self):
        self.agente.procesar("avanza 0.1 metros")
        self.agente.procesar("repeti")
        self.assertEqual("MOVER", self.agente.ultima_accion_ejecutada.tipo)
        self.agente.procesar("otra vez")
        self.assertEqual("MOVER", self.agente.ultima_accion_ejecutada.tipo)

    def test_modo_lento_on_off(self):
        self.agente.procesar("modo lento")
        self.assertTrue(self.agente.modo_lento)
        self.agente.procesar("modo normal")
        self.assertFalse(self.agente.modo_lento)

    def test_modo_lento_no_excede_limite_y_conserva_distancia(self):
        self.agente.procesar("modo lento")
        r = self.agente.procesar("avanza 1 metro")
        self.assertLessEqual(r["parametros"]["velocidad_ms"], self.robot.perfil.velocidad_max)
        tiempo_total = sum(llamada[2] for llamada in self.robot.llamadas if llamada[0] == "avanzar")
        self.assertAlmostEqual(1.0, tiempo_total * r["parametros"]["velocidad_ms"])
        self.assertEqual(1.0, self.agente.ultima_accion_ejecutada.parametros["distancia_m"])
        self.assertNotIn("velocidad_ms", self.agente.ultima_accion_ejecutada.parametros)

    def test_reversa_de_avance(self):
        self.agente.procesar("avanza 0.1 metros")
        r = self.agente.procesar("reversa")
        self.assertEqual("atras", r["parametros"]["direccion"])
        self.assertLess(self.robot.llamadas[-1][1], 0)

    def test_reversa_de_retroceso(self):
        self.agente.procesar("retrocede 0.1 metros")
        r = self.agente.procesar("volve atras")
        self.assertEqual("adelante", r["parametros"]["direccion"])
        self.assertGreater(self.robot.llamadas[-1][1], 0)

    def test_reversa_giro_derecha(self):
        self.agente.procesar("gira 20 grados a la derecha")
        r = self.agente.procesar("reverti el ultimo movimiento")
        self.assertEqual("izquierda", r["parametros"]["direccion"])
        self.assertGreater(self.robot.llamadas[-1][1], 0)

    def test_reversa_giro_izquierda(self):
        self.agente.procesar("gira 20 grados a la izquierda")
        r = self.agente.procesar("deshace lo ultimo")
        self.assertEqual("derecha", r["parametros"]["direccion"])
        self.assertLess(self.robot.llamadas[-1][1], 0)

    def test_reversa_sin_historial(self):
        r = self.agente.procesar("reversa")
        self.assertFalse(r["ejecutar"])
        self.assertIn("no hay", r["mensaje"])

    def test_accion_no_reversible_no_destruye_movimiento(self):
        self.agente.procesar("avanza 0.1 metros")
        movimiento = self.agente.ultimo_movimiento_reversible
        self.agente.procesar("saluda")
        self.assertEqual(movimiento, self.agente.ultimo_movimiento_reversible)

    def test_replay_se_bloquea_si_cambian_los_limites(self):
        self.agente.procesar("avanza 0.2 metros a 0.2 m/s")
        perfil_mas_estricto = type(
            "PerfilMasEstricto", (), {
                "nombre": "estricto", "velocidad_max": 0.1,
                "velocidad_angular_max": 0.5, "duracion_max": 5.0,
                "bateria_min": 25,
            },
        )()
        self.agente.validador.perfil = perfil_mas_estricto
        r = self.agente.procesar("repeti")
        self.assertTrue(r["bloqueado"])
        self.assertFalse(r["ejecutar"])


if __name__ == "__main__":
    unittest.main()

