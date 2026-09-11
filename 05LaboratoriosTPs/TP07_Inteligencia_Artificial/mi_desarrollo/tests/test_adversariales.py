import random
import sys
import unittest
from unittest.mock import patch

from configuracion import directorio_modelos
from mi_tp07 import AgenteRobot
from voz import (
    CapturadorMicrofono,
    ErrorVoz,
    MetricasSTT,
    TranscriptorFasterWhisper,
    evaluar_confianza,
)


class PerfilFalso:
    velocidad_max = 0.2
    velocidad_angular_max = 0.5
    duracion_max = 5.0
    bateria_min = 25


class RobotSinBateria:
    perfil = PerfilFalso()

    def verificar_estado(self):
        return {}


class RobotEjecutorFallido:
    perfil = PerfilFalso()

    def __init__(self):
        self.detenciones = 0

    def verificar_estado(self):
        return {"bateria": 80}

    def avanzar(self, **_kwargs):
        raise RuntimeError("transporte caido")

    def detenerse(self):
        self.detenciones += 1


class RobotRealSinTelemetriaConfirmada(RobotEjecutorFallido):
    destino = "g1"

    def avanzar(self, **_kwargs):
        raise AssertionError("no debe alcanzar locomocion real")


class EmotesActivosFalsos:
    activo = "BAILE"

    def __init__(self):
        self.cancelado = False

    def cancelar(self):
        self.cancelado = True

    def ejecutar_aleatorio(self, _chiste=None):
        return "BAILE"


class TTSDetenibleFalso:
    def __init__(self):
        self.detenido = False

    def hablar(self, _texto):
        return True

    def detener(self):
        self.detenido = True


class AdversarialesTests(unittest.TestCase):
    def test_cien_metros_en_palabras_se_bloquea(self):
        r = AgenteRobot().procesar("avanza cien metros")
        self.assertTrue(r["bloqueado"])
        self.assertEqual(100.0, r["parametros"]["distancia_m"])

    def test_numeros_hablados_se_interpretan_sin_caer_a_defaults(self):
        agente = AgenteRobot()
        distancia = agente.procesar("avanza cincuenta metros")
        angulo = agente.procesar("gira doscientos setenta grados")
        velocidad = agente.procesar("avanza a dos metros por segundo")
        self.assertEqual(50, distancia["parametros"]["distancia_m"])
        self.assertTrue(distancia["bloqueado"])
        self.assertEqual(270, angulo["parametros"]["angulo_deg"])
        self.assertTrue(angulo["bloqueado"])
        self.assertEqual(2, velocidad["parametros"]["velocidad_ms"])
        self.assertTrue(velocidad["bloqueado"])

    def test_unidad_con_numero_incomprensible_se_bloquea(self):
        r = AgenteRobot().procesar("avanza muchisimos metros")
        self.assertTrue(r["bloqueado"])
        self.assertIn("no reconocida", r["mensaje"])

    def test_robot_sin_bateria_falla_cerrado(self):
        robot = RobotSinBateria()
        # El ejecutor no llega a usar los metodos de movimiento: se bloquea antes.
        r = AgenteRobot(robot).procesar("avanza un poco")
        self.assertTrue(r["bloqueado"])
        self.assertIn("bateria desconocida", r["mensaje"])

    def test_robot_real_sin_telemetria_confirmada_queda_bloqueado(self):
        r = AgenteRobot(RobotRealSinTelemetriaConfirmada()).procesar("avanza un poco")
        self.assertTrue(r["bloqueado"])
        self.assertIn("telemetria", r["mensaje"])

    def test_ruido_silencio_y_transcripcion_vacia_no_son_comandos(self):
        for texto in ("", "shhh ruido ambiente"):
            ok, _ = evaluar_confianza(texto, MetricasSTT(0.99, -0.1, 0.01))
            self.assertFalse(ok)

    def test_parecido_fonetico_no_se_corrige_a_movimiento(self):
        ok, _ = evaluar_confianza("abanza", MetricasSTT(0.99, -0.1, 0.01))
        self.assertFalse(ok)
        self.assertFalse(AgenteRobot().procesar("abanza")["ejecutar"])

    def test_no_avances_tiene_prioridad_de_stop(self):
        r = AgenteRobot().procesar("no avances")
        self.assertEqual("DETENERSE", r["tipo"])
        self.assertTrue(r["ejecutar"])

    def test_negacion_no_dispara_repeticion(self):
        agente = AgenteRobot()
        agente.procesar("avanza un poco")
        r = agente.procesar("no repitas")
        self.assertEqual("DETENERSE", r["tipo"])

    def test_preposicion_para_atras_no_se_confunde_con_stop(self):
        r = AgenteRobot().procesar("anda para atras un metro")
        self.assertEqual("MOVER", r["tipo"])
        self.assertEqual("atras", r["parametros"]["direccion"])

    def test_verbo_peligroso_conjugado_bloquea_movimiento_combinado(self):
        r = AgenteRobot().procesar("avanza y despues empujar la caja")
        self.assertTrue(r["bloqueado"])
        self.assertIn("peligrosa", r["mensaje"])

    def test_tirate_un_chiste_no_es_confundido_con_accion_peligrosa(self):
        r = AgenteRobot(
            al_terminar_chiste=lambda _x: None, salida_tts=lambda _x: None
        ).procesar("tirate un chiste")
        self.assertTrue(r["ejecutar"])
        self.assertEqual("CONTAR_CHISTE", r["tipo"])

    def test_excepcion_del_ejecutor_falla_cerrado_y_frena(self):
        robot = RobotEjecutorFallido()
        r = AgenteRobot(robot).procesar("avanza un poco")
        self.assertTrue(r["bloqueado"])
        self.assertGreaterEqual(robot.detenciones, 1)

    def test_stop_cancela_presentacion_activa_en_limite_de_comando(self):
        emotes = EmotesActivosFalsos()
        tts = TTSDetenibleFalso()
        agente = AgenteRobot(tts=tts, emote_manager=emotes)
        r = agente.procesar("detenete")
        self.assertTrue(r["ejecutar"])
        self.assertTrue(tts.detenido)
        self.assertTrue(emotes.cancelado)

    def test_muchos_otros_chistes_no_repite_en_la_ronda(self):
        agente = AgenteRobot(
            rng=random.Random(55),
            al_terminar_chiste=lambda _x: None,
            salida_tts=lambda _x: None,
        )
        vistos = [
            agente.procesar("otro chiste")["parametros"]["chiste"]
            for _ in range(100)
        ]
        self.assertEqual(100, len(set(vistos)))

    def test_modo_lento_repetido_es_idempotente(self):
        agente = AgenteRobot()
        for _ in range(5):
            agente.procesar("modo lento")
        self.assertTrue(agente.modo_lento)
        for _ in range(5):
            agente.procesar("modo normal")
        self.assertFalse(agente.modo_lento)

    def test_modelo_ausente_da_error_controlado(self):
        with patch.dict(sys.modules, {"faster_whisper": None}):
            with self.assertRaisesRegex(ErrorVoz, "requirements-voz"):
                TranscriptorFasterWhisper()._cargar_modelo()

    def test_ausencia_de_microfono_devuelve_lista_vacia(self):
        class SoundDeviceSinEntradas:
            @staticmethod
            def query_devices(*_args):
                return []

        capturador = CapturadorMicrofono()
        with patch.object(
            capturador, "_dependencias", return_value=(object(), SoundDeviceSinEntradas())
        ):
            self.assertEqual([], capturador.listar_microfonos())

    def test_error_de_portaudio_se_convierte_en_error_voz(self):
        class SoundDeviceFallido:
            @staticmethod
            def query_devices(*_args):
                raise RuntimeError("PortAudio no disponible")

        capturador = CapturadorMicrofono()
        with patch.object(
            capturador, "_dependencias", return_value=(object(), SoundDeviceFallido())
        ):
            with self.assertRaisesRegex(ErrorVoz, "microfonos"):
                capturador.listar_microfonos()

    def test_ruta_de_modelos_dentro_del_repo_se_rechaza(self):
        ruta_interna = __import__("pathlib").Path(__file__).resolve().parents[2] / "modelos"
        with patch.dict("os.environ", {"TP07_MODEL_DIR": str(ruta_interna)}):
            with self.assertRaisesRegex(ValueError, "fuera del repositorio"):
                directorio_modelos()


if __name__ == "__main__":
    unittest.main()
