import random
import unittest

from capacidades_robot import CapacidadesRobot, detectar_capacidades
from emotes import (
    BackendEmotesRealConfirmado,
    BackendEmotesSimulador,
    CATALOGO_EMOTES,
    EmoteManager,
    crear_emote_manager,
)
from mi_tp07 import AgenteRobot


class PerfilFalso:
    bateria_min = 25


class RobotFalso:
    perfil = PerfilFalso()

    def __init__(self, bateria=80, destino="g1"):
        self.bateria = bateria
        self.destino = destino
        self.detenciones = 0

    def detenerse(self):
        self.detenciones += 1

    def verificar_estado(self):
        return {"bateria": self.bateria}


class ArmClientFalso:
    def __init__(self, falla=False):
        self.falla = falla
        self.acciones = []
        self.cancelaciones = 0

    def GetActionList(self):
        return 0, ["hands up", "release arm"]

    def ExecuteActionByName(self, nombre):
        self.acciones.append(nombre)
        if self.falla and nombre != "release arm":
            raise RuntimeError("fallo simulado")
        return 0

    def StopCustomAction(self):
        self.cancelaciones += 1


class BackendCuenta:
    def __init__(self, falla=False):
        self.nombres = []
        self.falla = falla
        self.cancelado = False

    def ejecutar(self, emote):
        self.nombres.append(emote.nombre)
        if self.falla:
            raise RuntimeError("falla esperada")

    def cancelar(self):
        self.cancelado = True


def capacidades_reales(arm):
    return detectar_capacidades(
        RobotFalso(),
        {
            "variante_confirmada": True,
            "manos_confirmadas": True,
            "firmware_confirmado": True,
            "sdk_confirmado": True,
            "telemetria_bateria_confirmada": True,
        },
        arm,
    )


class EmotesTests(unittest.TestCase):
    def test_capability_detection_es_conservadora(self):
        desconocidas = detectar_capacidades(RobotFalso())
        self.assertFalse(desconocidas.hardware_confirmado)
        arm = ArmClientFalso()
        confirmadas = capacidades_reales(arm)
        self.assertTrue(confirmadas.hardware_confirmado)
        self.assertEqual(
            frozenset({"hands up", "release arm"}), confirmadas.acciones_nativas
        )

    def test_simulador_tiene_los_seis_emotes(self):
        capacidades = detectar_capacidades(RobotFalso(destino="simulador"))
        manager = EmoteManager(capacidades, BackendCuenta(), random.Random(1))
        self.assertEqual(6, len(manager.disponibles()))

    def test_real_solo_expone_accion_nativa_confirmada(self):
        robot, arm = RobotFalso(), ArmClientFalso()
        capacidades = capacidades_reales(arm)
        backend = BackendEmotesRealConfirmado(robot, arm, capacidades)
        manager = EmoteManager(capacidades, backend, random.Random(1))
        self.assertEqual(
            ["APUNTAR_CIELO_DOS_BRAZOS"],
            [emote.nombre for emote in manager.disponibles()],
        )

    def test_no_repite_consecutivamente_en_simulacion(self):
        capacidades = CapacidadesRobot(es_simulacion=True)
        backend = BackendCuenta()
        manager = EmoteManager(capacidades, backend, random.Random(5))
        elegidos = [manager.ejecutar_aleatorio() for _ in range(30)]
        self.assertTrue(all(a != b for a, b in zip(elegidos, elegidos[1:])))

    def test_backend_simulador_genera_evento_semantico(self):
        salida = []
        manager = crear_emote_manager(
            CapacidadesRobot(es_simulacion=True),
            rng=random.Random(2), salida=salida.append,
        )
        nombre = manager.ejecutar_aleatorio()
        self.assertEqual([f"[EMOTE] {nombre}"], salida)

    def test_backend_real_mockeado_detiene_ejecuta_y_vuelve_neutral(self):
        robot, arm = RobotFalso(), ArmClientFalso()
        capacidades = capacidades_reales(arm)
        backend = BackendEmotesRealConfirmado(robot, arm, capacidades)
        manager = EmoteManager(capacidades, backend)
        self.assertTrue(manager.ejecutar("APUNTAR_CIELO_DOS_BRAZOS"))
        self.assertEqual(1, robot.detenciones)
        self.assertEqual(["hands up", "release arm"], arm.acciones)

    def test_excepcion_real_intenta_neutral_y_no_se_propaga(self):
        salida = []
        robot, arm = RobotFalso(), ArmClientFalso(falla=True)
        capacidades = capacidades_reales(arm)
        backend = BackendEmotesRealConfirmado(robot, arm, capacidades)
        manager = EmoteManager(capacidades, backend, salida=salida.append)
        self.assertFalse(manager.ejecutar("APUNTAR_CIELO_DOS_BRAZOS"))
        self.assertEqual("release arm", arm.acciones[-1])
        self.assertIn("ERROR", salida[-1])

    def test_cancelar_backend_real_detiene_y_neutraliza(self):
        robot, arm = RobotFalso(), ArmClientFalso()
        capacidades = capacidades_reales(arm)
        manager = EmoteManager(
            capacidades, BackendEmotesRealConfirmado(robot, arm, capacidades)
        )
        manager.cancelar()
        self.assertEqual(1, robot.detenciones)
        self.assertEqual(1, arm.cancelaciones)
        self.assertEqual("release arm", arm.acciones[-1])

    def test_chiste_dispara_exactamente_un_emote(self):
        backend = BackendCuenta()
        manager = EmoteManager(
            CapacidadesRobot(es_simulacion=True), backend, random.Random(8)
        )
        agente = AgenteRobot(emote_manager=manager, salida_tts=lambda _x: None)
        agente.procesar("contame un chiste")
        self.assertEqual(1, len(backend.nombres))

    def test_error_emote_no_rompe_el_siguiente_comando(self):
        manager = EmoteManager(
            CapacidadesRobot(es_simulacion=True), BackendCuenta(falla=True),
            salida=lambda _x: None,
        )
        agente = AgenteRobot(emote_manager=manager, salida_tts=lambda _x: None)
        self.assertTrue(agente.procesar("contame un chiste")["ejecutar"])
        self.assertTrue(agente.procesar("modo lento")["ejecutar"])

    def test_catalogo_no_declara_angulos(self):
        self.assertEqual(6, len(CATALOGO_EMOTES))
        self.assertTrue(all("angulo" not in vars(e) for e in CATALOGO_EMOTES))


if __name__ == "__main__":
    unittest.main()
