import random
import unittest

from capacidades_robot import CapacidadesRobot
from chistes import BolsaChistes, CHISTES
from mi_tp07 import AgenteRobot
from tts import TTSConFallback, TTSConsola, TTSUnitreeConfirmado


class TTSFalso:
    def __init__(self, falla=False):
        self.falla = falla
        self.textos = []

    def hablar(self, texto):
        if self.falla:
            raise RuntimeError("falla esperada")
        self.textos.append(texto)
        return True

    def detener(self):
        return None


class AudioClientFalso:
    def __init__(self):
        self.llamadas = []

    def TtsMaker(self, texto, speaker_id):
        self.llamadas.append((texto, speaker_id))
        return 0


class ChistesYTTSSTests(unittest.TestCase):
    def test_hay_exactamente_100_chistes_no_vacios_y_unicos(self):
        self.assertEqual(100, len(CHISTES))
        self.assertEqual(100, len(set(CHISTES)))
        self.assertTrue(all(isinstance(c, str) and c.strip() for c in CHISTES))

    def test_bolsa_no_repite_antes_de_agotarse_ni_en_la_frontera(self):
        bolsa = BolsaChistes(random.Random(7))
        ronda = [bolsa.siguiente() for _ in range(100)]
        siguiente = bolsa.siguiente()
        self.assertEqual(100, len(set(ronda)))
        self.assertNotEqual(ronda[-1], siguiente)

    def test_seed_es_determinista(self):
        a = BolsaChistes(random.Random(123))
        b = BolsaChistes(random.Random(123))
        self.assertEqual(
            [a.siguiente() for _ in range(10)],
            [b.siguiente() for _ in range(10)],
        )

    def test_intencion_contar_chiste_y_tts_mockeable(self):
        tts = TTSFalso()
        agente = AgenteRobot(tts=tts, rng=random.Random(1))
        r = agente.procesar("contame un chiste")
        self.assertEqual("CONTAR_CHISTE", r["tipo"])
        self.assertTrue(r["ejecutar"])
        self.assertEqual([r["parametros"]["chiste"]], tts.textos)

    def test_repetir_dice_el_mismo_chiste_y_otro_consume_uno_nuevo(self):
        tts = TTSFalso()
        agente = AgenteRobot(tts=tts, rng=random.Random(2))
        primero = agente.procesar("decime un chiste")["parametros"]["chiste"]
        repetido = agente.procesar("repeti")["parametros"]["chiste"]
        otro = agente.procesar("otro chiste")["parametros"]["chiste"]
        self.assertEqual(primero, repetido)
        self.assertNotEqual(primero, otro)

    def test_chiste_no_destruye_ultimo_movimiento(self):
        agente = AgenteRobot(tts=TTSFalso(), rng=random.Random(3))
        agente.procesar("avanza 1 metro")
        movimiento = agente.ultimo_movimiento_reversible
        agente.procesar("haceme reir")
        self.assertEqual(movimiento, agente.ultimo_movimiento_reversible)

    def test_fallback_a_consola_si_tts_falla(self):
        salida = []
        tts = TTSConFallback(TTSFalso(falla=True), TTSConsola(salida.append))
        self.assertTrue(tts.hablar("prueba"))
        self.assertEqual(["[ROBOT] prueba"], salida)

    def test_error_tts_no_rompe_el_agente(self):
        salida = []
        agente = AgenteRobot(tts=TTSFalso(falla=True), salida_tts=salida.append)
        r = agente.procesar("tirate un chiste")
        self.assertTrue(r["ejecutar"])
        self.assertEqual(1, len(salida))

    def test_cliente_unitree_confirmado_puede_mockearse(self):
        capacidades = CapacidadesRobot(
            es_simulacion=False,
            variante_confirmada=True,
            manos_confirmadas=True,
            firmware_confirmado=True,
            sdk_confirmado=True,
            tts_nativo=True,
        )
        cliente = AudioClientFalso()
        tts = TTSUnitreeConfirmado(cliente, capacidades, speaker_id=0)
        self.assertTrue(tts.hablar("hola"))
        self.assertEqual([("hola", 0)], cliente.llamadas)


if __name__ == "__main__":
    unittest.main()

