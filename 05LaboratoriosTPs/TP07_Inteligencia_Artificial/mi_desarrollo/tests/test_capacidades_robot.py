import unittest

from capacidades_robot import (
    CapacidadesRobot,
    capacidades_hardware_desconocido,
    capacidades_simulador,
)


class CapacidadesRobotTests(unittest.TestCase):
    def test_simulacion_permite_probar_emotes(self):
        self.assertTrue(capacidades_simulador().permite_emote_fisico())

    def test_hardware_desconocido_bloquea_emotes(self):
        capacidades = capacidades_hardware_desconocido()
        self.assertFalse(capacidades.hardware_confirmado)
        self.assertFalse(capacidades.permite_emote_fisico("cualquier_accion"))

    def test_hardware_confirmado_exige_accion_descubierta(self):
        capacidades = CapacidadesRobot(
            es_simulacion=False,
            variante_confirmada=True,
            manos_confirmadas=True,
            firmware_confirmado=True,
            sdk_confirmado=True,
            telemetria_bateria_confirmada=True,
            acciones_nativas=frozenset({"accion_verificada"}),
        )
        self.assertTrue(capacidades.permite_emote_fisico("accion_verificada"))
        self.assertFalse(capacidades.permite_emote_fisico("accion_inventada"))


if __name__ == "__main__":
    unittest.main()
