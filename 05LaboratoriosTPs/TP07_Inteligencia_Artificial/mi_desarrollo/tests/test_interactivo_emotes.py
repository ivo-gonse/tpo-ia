import unittest
from unittest.mock import Mock, patch

import evaluar as modulo_evaluar
from capacidades_robot import CapacidadesRobot
from emotes import EmoteManager
from mi_tp07 import AgenteRobot, main


class BackendCuenta:
    def __init__(self):
        self.nombres = []

    def ejecutar(self, emote):
        self.nombres.append(emote.nombre)

    def cancelar(self):
        pass


class TTSCuenta:
    def __init__(self):
        self.textos = []

    def hablar(self, texto):
        self.textos.append(texto)
        return True

    def detener(self):
        pass


def crear_agente_controlado():
    backend = BackendCuenta()
    tts = TTSCuenta()
    manager = EmoteManager(
        CapacidadesRobot(es_simulacion=True),
        backend,
        hablar=tts.hablar,
        salida=lambda _texto: None,
    )
    return AgenteRobot(tts=tts, emote_manager=manager), backend, tts


class ParserEmotesTests(unittest.TestCase):
    def test_numeros_digitos_y_palabras(self):
        esperados = (
            ("RISA", "1", "uno"),
            ("BAILE", "2", "dos"),
            ("BRAZOS_CRUZADOS_COSTADO", "3", "tres"),
            ("PULGAR_ARRIBA", "4", "cuatro"),
            ("APUNTAR_CIELO_DOS_BRAZOS", "5", "cinco"),
            ("FINGER_GUNS_BANG_BANG", "6", "seis"),
        )
        agente, backend, _tts = crear_agente_controlado()
        for esperado, digito, palabra in esperados:
            for frase in (f"emote {digito}", f"hacé el emote {palabra}"):
                with self.subTest(frase=frase):
                    resultado = agente.procesar(frase)
                    self.assertEqual("EJECUTAR_EMOTE", resultado["tipo"])
                    self.assertEqual(esperado, resultado["parametros"]["emote"])
                    self.assertEqual(esperado, backend.nombres[-1])

    def test_variantes_textuales_minimas(self):
        casos = {
            "RISA": (
                "risa", "reíte", "hacé risa", "hacé el de la risa",
            ),
            "BAILE": (
                "baile", "bailá", "baila", "hacé un baile", "ponete a bailar",
            ),
            "BRAZOS_CRUZADOS_COSTADO": (
                "brazos cruzados", "cruzate de brazos", "hacete el canchero",
                "ponete de costado",
            ),
            "PULGAR_ARRIBA": (
                "pulgar arriba", "like", "hacé like", "aprobado",
            ),
            "APUNTAR_CIELO_DOS_BRAZOS": (
                "apuntá al cielo", "brazos arriba", "señalá arriba",
                "apuntá arriba con los dos brazos",
            ),
            "FINGER_GUNS_BANG_BANG": (
                "pistolas", "hacé las pistolas", "finger guns", "bang bang",
                "dispará con las manos",
            ),
        }
        agente, backend, _tts = crear_agente_controlado()
        for esperado, frases in casos.items():
            for frase in frases:
                with self.subTest(frase=frase):
                    resultado = agente.procesar(frase)
                    self.assertEqual("EJECUTAR_EMOTE", resultado["tipo"])
                    self.assertEqual(esperado, resultado["parametros"]["emote"])
                    self.assertEqual(esperado, backend.nombres[-1])

    def test_ayuda_es_breve_y_no_reemplaza_ultima_accion(self):
        agente, _backend, _tts = crear_agente_controlado()
        agente.procesar("baile")
        ultima = agente.ultima_accion_ejecutada
        for frase in ("ayuda", "help", "comandos"):
            with self.subTest(frase=frase):
                resultado = agente.procesar(frase)
                self.assertEqual("AYUDA", resultado["tipo"])
                self.assertIn("MOVIMIENTO", resultado["mensaje"])
                self.assertIn("ENTRETENIMIENTO", resultado["mensaje"])
                self.assertIs(ultima, agente.ultima_accion_ejecutada)


class ChisteCompuestoTests(unittest.TestCase):
    def test_chiste_solo_y_generico_disparan_un_solo_emote(self):
        agente, backend, _tts = crear_agente_controlado()
        for frase in (
            "contame un chiste",
            "decime un chiste y hacé un emote",
            "chiste y emote",
            "haceme reír y después hacé un emote",
        ):
            with self.subTest(frase=frase):
                antes = len(backend.nombres)
                resultado = agente.procesar(frase)
                self.assertEqual("CONTAR_CHISTE", resultado["tipo"])
                self.assertEqual(antes + 1, len(backend.nombres))
                self.assertEqual(backend.nombres[-1], resultado["parametros"]["emote"])

    def test_chiste_con_emote_especifico_no_agrega_un_aleatorio(self):
        casos = (
            ("decime un chiste y después bailá", "BAILE"),
            ("contame un chiste y hacé el pulgar arriba", "PULGAR_ARRIBA"),
            ("contame un chiste y hacé el emote 4", "PULGAR_ARRIBA"),
        )
        agente, backend, _tts = crear_agente_controlado()
        for frase, esperado in casos:
            with self.subTest(frase=frase):
                antes = len(backend.nombres)
                resultado = agente.procesar(frase)
                self.assertEqual(antes + 1, len(backend.nombres))
                self.assertEqual(esperado, backend.nombres[-1])
                self.assertEqual(esperado, resultado["parametros"]["emote"])


class PerfilFalso:
    velocidad_max = 0.2
    velocidad_angular_max = 0.5
    duracion_max = 5.0
    bateria_min = 25


class RobotInicioFalso:
    destino = "simulador"
    transporte = "local"
    modelo = "g1"
    perfil = PerfilFalso()

    def __init__(self):
        self.eventos = []

    def conectar(self):
        self.eventos.append("conectar")

    def detenerse(self):
        self.eventos.append("detenerse")

    def desconectar(self):
        self.eventos.append("desconectar")

    def ejecutar_emote_simulado(self, _nombre):
        raise AssertionError("no debe ejecutar emotes durante el arranque")

    def cancelar_emote_simulado(self):
        pass


class InicioInteractivoTests(unittest.TestCase):
    def test_inicio_normal_solo_conecta_frena_y_espera_input(self):
        robot = RobotInicioFalso()
        entrada = Mock(return_value="")
        with (
            patch("mi_tp07.Robot", return_value=robot),
            patch("builtins.input", entrada),
            patch("builtins.print") as salida,
            patch.object(modulo_evaluar, "evaluar") as evaluar_mock,
        ):
            codigo = main([])
        self.assertEqual(0, codigo)
        self.assertEqual(["conectar", "detenerse", "desconectar"], robot.eventos)
        self.assertEqual(1, entrada.call_count)
        evaluar_mock.assert_not_called()
        impreso = "\n".join(" ".join(map(str, llamada.args)) for llamada in salida.call_args_list)
        self.assertIn("=== AGENTE G1 ===", impreso)
        self.assertIn("Esperando orden", impreso)

    def test_evaluacion_solo_se_activa_con_bandera_y_no_conecta(self):
        with (
            patch("mi_tp07.Robot") as robot_factory,
            patch.object(modulo_evaluar, "evaluar") as evaluar_mock,
        ):
            codigo = main(["--evaluar"])
        self.assertEqual(0, codigo)
        robot_factory.assert_not_called()
        evaluar_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
