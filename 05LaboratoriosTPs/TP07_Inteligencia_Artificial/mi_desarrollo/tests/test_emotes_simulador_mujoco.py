import sys
from pathlib import Path
import unittest


ENTORNO = Path(__file__).resolve().parents[2] / "entorno"
if str(ENTORNO) not in sys.path:
    sys.path.insert(0, str(ENTORNO))

from sim.emotes_g1 import (  # noqa: E402
    AnimadorEmotesG1,
    JOINTS_SUPERIORES,
    NOMBRES_EMOTES,
    duracion_emote,
    obtener_animacion,
)
from sim.local import ClienteLocal, ServidorLocal  # noqa: E402
from sim.mundo import Mundo  # noqa: E402
from sim.robots import G1  # noqa: E402
from sim.safety import perfil  # noqa: E402
from sim.simulador import SimuladorLocal  # noqa: E402
from capacidades_robot import CapacidadesRobot  # noqa: E402
from emotes import crear_emote_manager  # noqa: E402


class EmotesMuJoCoTests(unittest.TestCase):
    def setUp(self):
        self.mundo = Mundo(perfil("tp07"))
        self.sim = SimuladorLocal(
            self.mundo, G1, repo="", verboso=False, puerto=0
        )
        self.sim._escribir_pose()
        self.neutral = self.sim.data.qpos.copy()

    def _ir_al_medio(self, nombre):
        duracion = duracion_emote(nombre)
        self.mundo.iniciar_emote(nombre, duracion)
        self.mundo.avanzar(duracion * 0.5)
        self.sim._escribir_pose()
        return self.sim.data.qpos.copy()

    def _terminar(self, nombre):
        self.mundo.avanzar(duracion_emote(nombre) * 0.51)
        self.sim._escribir_pose()
        return self.sim.data.qpos.copy()

    def test_cada_emote_cambia_joints_reales_y_vuelve_a_neutral(self):
        for nombre in NOMBRES_EMOTES:
            with self.subTest(emote=nombre):
                medio = self._ir_al_medio(nombre)
                direcciones = self.sim.animador_emotes.direcciones_qpos
                usados = self.sim.animador_emotes.joints_modificados(nombre)
                self.assertTrue(
                    any(
                        abs(float(medio[direcciones[j]]) - float(self.neutral[direcciones[j]]))
                        > 1e-7
                        for j in usados
                    )
                )
                final = self._terminar(nombre)
                self.assertIsNone(self.mundo.leer()["emote"])
                self.assertLess(max(abs(final - self.neutral)), 1e-9)

    def test_emotes_no_mueven_root_ni_piernas(self):
        for nombre in NOMBRES_EMOTES:
            with self.subTest(emote=nombre):
                medio = self._ir_al_medio(nombre)
                self.assertLess(max(abs(medio[:7] - self.neutral[:7])), 1e-12)
                # En este modelo compilado las piernas ocupan qpos 7..18.
                self.assertLess(max(abs(medio[7:19] - self.neutral[7:19])), 1e-12)
                estado = self.mundo.leer()
                self.assertEqual((0.0, 0.0, 0.0), (estado["x"], estado["y"], estado["yaw"]))
                self._terminar(nombre)

    def test_detener_cancela_y_neutraliza(self):
        self._ir_al_medio("BAILE")
        self.mundo.detener()
        self.sim._escribir_pose()
        self.assertIsNone(self.mundo.leer()["emote"])
        self.assertLess(max(abs(self.sim.data.qpos - self.neutral)), 1e-9)

    def test_error_durante_animacion_recupera_neutral(self):
        real = self.sim.animador_emotes

        class AnimadorQueFalla:
            direcciones_qpos = real.direcciones_qpos

            def aplicar(self, qpos, _nombre, _progreso):
                qpos[self.direcciones_qpos["waist_yaw_joint"]] = 0.4
                raise RuntimeError("falla inyectada")

        self.sim.animador_emotes = AnimadorQueFalla()
        self.mundo.iniciar_emote("RISA", duracion_emote("RISA"))
        self.mundo.avanzar(0.2)
        self.sim._escribir_pose()
        self.assertIsNone(self.mundo.leer()["emote"])
        self.assertLess(max(abs(self.sim.data.qpos - self.neutral)), 1e-9)

    def test_indices_se_resuelven_desde_el_modelo_compilado(self):
        animador = AnimadorEmotesG1(self.sim.model, self.sim.mj)
        self.assertEqual(19, animador.direcciones_qpos["waist_yaw_joint"])
        self.assertEqual(22, animador.direcciones_qpos["left_shoulder_pitch_joint"])
        self.assertEqual(35, animador.direcciones_qpos["right_wrist_yaw_joint"])
        self.assertFalse(animador.tiene_dedos_articulados)

    def test_keyframes_solo_declaran_joints_superiores_permitidos(self):
        for nombre in NOMBRES_EMOTES:
            with self.subTest(emote=nombre):
                declarados = {
                    joint
                    for fotograma in obtener_animacion(nombre).fotogramas
                    for joint in fotograma.pose
                }
                self.assertLessEqual(declarados, JOINTS_SUPERIORES)

    def test_cruzados_y_cielo_no_generan_contactos_entre_geoms(self):
        for nombre in ("BRAZOS_CRUZADOS_COSTADO", "APUNTAR_CIELO_DOS_BRAZOS"):
            with self.subTest(emote=nombre):
                self.sim.data.qpos[:] = self.neutral
                self.sim.animador_emotes.aplicar(self.sim.data.qpos, nombre, 0.5)
                self.sim.mj.mj_forward(self.sim.model, self.sim.data)
                self.assertEqual(0, self.sim.data.ncon)

    def test_animaciones_muestreadas_no_atraviesan_geoms(self):
        for nombre in NOMBRES_EMOTES:
            for paso in range(41):
                progreso = paso / 40
                with self.subTest(emote=nombre, progreso=progreso):
                    self.sim.data.qpos[:] = self.neutral
                    self.sim.animador_emotes.aplicar(
                        self.sim.data.qpos, nombre, progreso,
                    )
                    self.sim.mj.mj_forward(self.sim.model, self.sim.data)
                    self.assertEqual(0, self.sim.data.ncon)

    def test_finger_guns_tiene_preparacion_disparos_y_recoil(self):
        animacion = obtener_animacion("FINGER_GUNS_BANG_BANG")
        self.assertGreaterEqual(len(animacion.fotogramas), 8)
        poses = [dict(fotograma.pose) for fotograma in animacion.fotogramas]
        self.assertGreaterEqual(len({tuple(sorted(pose.items())) for pose in poses}), 4)


class ProtocoloEmotesSimuladosTests(unittest.TestCase):
    def test_socket_inicia_y_stopmove_cancela(self):
        mundo = Mundo(perfil("tp07"))
        servidor = ServidorLocal(
            mundo, G1, perfil("tp07"), verboso=False, puerto=0
        )
        cliente = ClienteLocal(puerto=servidor.puerto)
        servidor.arrancar_en_hilo()
        try:
            cliente.Init()
            duracion = cliente.EjecutarEmoteSimulado("RISA")
            self.assertGreater(duracion, 0.0)
            self.assertEqual("RISA", cliente.Estado()["emote"])
            cliente.StopMove()
            self.assertIsNone(cliente.Estado()["emote"])
        finally:
            cliente.Cerrar()
            servidor.shutdown()
            servidor.server_close()

    def test_manager_detecta_adapter_y_dispara_tts_despues_de_iniciar_pose(self):
        eventos = []

        class RobotSemanticoFalso:
            destino = "simulador"
            transporte = "local"
            modelo = "g1"

            def ejecutar_emote_simulado(self, nombre):
                eventos.append(("emote", nombre))

            def cancelar_emote_simulado(self):
                eventos.append(("cancelar", None))

        manager = crear_emote_manager(
            CapacidadesRobot(es_simulacion=True),
            robot=RobotSemanticoFalso(),
            hablar=lambda texto: eventos.append(("tts", texto)),
            salida=lambda _texto: None,
        )
        self.assertTrue(manager.ejecutar("FINGER_GUNS_BANG_BANG"))
        self.assertEqual(
            [("emote", "FINGER_GUNS_BANG_BANG"), ("tts", "bang bang")],
            eventos,
        )


if __name__ == "__main__":
    unittest.main()
