# =====================================================================
#  TP07 - Inteligencia Artificial
#  Agente que interpreta comandos en lenguaje natural
#
#  ESTE ES EL ARCHIVO DONDE ESCRIBIS TU PROGRAMA.
#
#  Antes de ejecutarlo:
#    1. Abri INICIAR_SIMULADOR (elegi G1 o Go2)
#    2. Espera a que aparezca la ventana con el robot
#    3. Recien ahi ejecuta este archivo
#
#  Nombre y apellido:  .....................................
#  Comision:           .....................................
# =====================================================================

import math
import re
import unicodedata

from robot import Robot

from capacidades_robot import detectar_capacidades
from chistes import BolsaChistes
from emotes import crear_emote_manager, resolver_emote
from ejecutor import Ejecutor
from estado_agente import AccionUsuario, EstadoAgente, invertir_movimiento
from tts import TTSConFallback, TTSConsola, crear_tts

# Pone tu nombre: aparece en el reporte que entregas.
ALUMNO = "Apellido, Nombre"

AYUDA_BREVE = """MOVIMIENTO
  avanzá 1 metro | girá 45 grados a la derecha | detente
MODOS
  modo lento | modo normal | repetí | reversa
ENTRETENIMIENTO
  contame un chiste | baile | emote 1..6"""


# =====================================================================
#  ETAPA 1 - CLASIFICADOR DE INTENCION
# =====================================================================
class ClasificadorIntencion:
    """Decide QUE quiere el usuario, sin mirar los numeros todavia."""

    TIPOS = (
        "MOVER", "GIRAR", "DETENERSE", "SALUDO", "CONSULTAR_ESTADO",
        "REPETIR_ULTIMA_ACCION", "REVERSA", "MODO_LENTO", "MODO_NORMAL",
        "CONTAR_CHISTE", "EJECUTAR_EMOTE", "AYUDA", "DESCONOCIDO",
    )

    def __init__(self):
        self.modelo = None

        # -------------------------------------------------------------
        #  NIVEL 2 (extension): entrenar un modelo con TU dataset.
        #
        #  Armas dataset.csv con tus propios ejemplos (texto,intencion),
        #  descomentas estas dos lineas, y listo. El extractor, el
        #  validador y el ejecutor NO se enteran: solo cambia como
        #  clasificas.
        #
        #  Antes de esto, corre `python3 entrenar.py` para ver tus
        #  metricas y que te avise si al dataset le falta algo.
        # -------------------------------------------------------------
        # from entrenar import entrenar_desde_csv
        # self.modelo = entrenar_desde_csv()

    def clasificar(self, texto):
        """Devuelve uno de los seis tipos de TIPOS.

        Tiene que aguantar variantes del espanol rioplatense:

            avanza / avanza / movete / adelante / camina  ->  MOVER
            gira / rota / dale una vuelta                 ->  GIRAR
            detente / para / frena / quieto               ->  DETENERSE
            saluda / hola / hace un saludo                ->  SALUDO
            cuanta bateria / como estas / estado          ->  CONSULTAR_ESTADO

        Todo lo que no reconozcas: DESCONOCIDO. Es una respuesta valida y
        correcta, no una derrota.

        El modulo `re` alcanza para esto. Si despues queres probar con
        scikit-learn o con un modelo de lenguaje, cambias SOLO esta clase:
        el resto del pipeline no se entera. Esa es la gracia de que las
        etapas sean independientes.

        Si entrenaste un modelo (nivel 2), aca lo usas:

            if self.modelo is not None:
                return self.modelo.predict([texto])[0]

        Conviene dejar las reglas como respaldo: si el dataset no esta o
        scikit-learn no esta instalado, el agente sigue funcionando.
        """
        normalizado = _normalizar(texto)

        # Las ordenes de control tienen prioridad sobre palabras de movimiento.
        if re.search(
            r"\b(no (?:avanza|avances|avanzar|te muevas)|"
            r"deten(?:te|ete|erse)?|frena|quiet[oa])\b",
            normalizado,
        ) or re.search(r"(?:^|\s)para(?:\s+(?:todo|ya|ahi|ahora))?(?:$|[.!?])", normalizado):
            return "DETENERSE"
        if any(frase in normalizado for frase in (
            "no repeti", "no repitas", "no lo hagas de nuevo", "no otra vez",
        )):
            return "DETENERSE"
        if any(frase in normalizado for frase in (
            "repeti", "repetir la ultima accion", "hacelo de nuevo", "otra vez", "de nuevo",
        )):
            return "REPETIR_ULTIMA_ACCION"
        if any(frase in normalizado for frase in (
            "reversa", "deshace lo ultimo", "reverti el ultimo movimiento", "volve atras",
        )):
            return "REVERSA"
        if any(frase in normalizado for frase in (
            "modo normal", "desactiva modo lento",
        )):
            return "MODO_NORMAL"
        if any(frase in normalizado for frase in (
            "modo lento", "activa modo lento", "mas despacio",
        )):
            return "MODO_LENTO"
        # Primero se reconoce la acción compuesta. El extractor decidirá si
        # corresponde un emote concreto o una selección aleatoria.
        if re.search(r"\bchiste\b", normalizado) or "haceme reir" in normalizado:
            return "CONTAR_CHISTE"
        if re.search(r"\b(ayuda|help|comandos)\b", normalizado):
            return "AYUDA"
        if resolver_emote(normalizado) is not None:
            return "EJECUTAR_EMOTE"
        if re.search(r"\b(bateria|estado)\b", normalizado):
            return "CONSULTAR_ESTADO"
        if re.search(r"\b(saluda|saludo)\b", normalizado):
            return "SALUDO"
        if "media vuelta" in normalizado or re.search(r"\b(gira|girar|rota|rotar)\b", normalizado):
            return "GIRAR"
        if re.search(
            r"\b(avanza|avanzar|muevete|mover|camina|caminar|anda|andar|retrocede|retroceder)\b",
            normalizado,
        ):
            return "MOVER"
        return "DESCONOCIDO"


# =====================================================================
#  ETAPA 2 - EXTRACTOR DE PARAMETROS
# =====================================================================
class ExtractorParametros:
    """Saca los numeros del texto. Sigue en unidades humanas."""

    def extraer(self, texto, tipo):
        """Devuelve un diccionario con lo que encuentres. Todo es opcional.

            {"distancia_m": 2.0}                  de "2 metros"
            {"angulo_deg": 90}                    de "90 grados" o "90 grados"
            {"velocidad_ms": 0.2}                 de "a 0.2 m/s"
            {"direccion": "derecha"}              de "a la derecha"
            {"direccion": "atras"}                de "retrocede"

        Ojo con los adverbios, que no traen numero:

            "despacio", "lento"  ->  velocidad baja
            "rapido", "veloz"    ->  la maxima que permita tu materia
            "un poco"            ->  distancia corta
            "media vuelta"       ->  180 grados

        IMPORTANTE: aca seguis en metros y grados, porque asi habla la
        gente. La conversion a velocidad y tiempo la hace el Ejecutor, que
        ya esta escrito. Vos no la haces.
        """
        normalizado = _normalizar(texto)
        parametros = {}

        if tipo == "MOVER":
            distancia = re.search(
                r"(-?\d+(?:[.,]\d+)?)\s*"
                r"(?:metros?(?!\s+por\s+segundo)|m\b(?!\s*/\s*s))",
                normalizado,
            )
            velocidad = re.search(
                r"(-?\d+(?:[.,]\d+)?)\s*"
                r"(?:m\s*/\s*s|metros?\s+por\s+segundo)",
                normalizado,
            )
            distancia_palabras = _numero_antes_de_unidad(
                normalizado, ("metro", "metros"), excluir_velocidad=True
            )
            velocidad_palabras = _numero_antes_de_frase(
                normalizado, (("metro", "por", "segundo"), ("metros", "por", "segundo"))
            )
            if distancia:
                parametros["distancia_m"] = float(distancia.group(1).replace(",", "."))
            elif distancia_palabras is not None:
                parametros["distancia_m"] = distancia_palabras
            elif "un poco" in normalizado:
                parametros["distancia_m"] = 0.3
            elif re.search(r"\bmetros?\b", normalizado) and not re.search(
                r"\bmetros?\s+por\s+segundo\b", normalizado
            ):
                parametros["_parametro_incierto"] = "distancia no reconocida"

            if velocidad:
                parametros["velocidad_ms"] = float(velocidad.group(1).replace(",", "."))
            elif velocidad_palabras is not None:
                parametros["velocidad_ms"] = velocidad_palabras
            elif re.search(r"\bmetros?\s+por\s+segundo\b", normalizado):
                parametros["_parametro_incierto"] = "velocidad no reconocida"
            elif re.search(r"\b(despacio|lento|lentamente)\b", normalizado):
                parametros["velocidad_ms"] = 0.1
            elif re.search(r"\b(rapido|veloz)\b", normalizado):
                # Rapido significa el maximo conservador del TP07, no el techo fisico.
                parametros["velocidad_ms"] = 0.2

            if re.search(r"\b(atras|retrocede|retroceder)\b", normalizado):
                parametros["direccion"] = "atras"
            else:
                parametros["direccion"] = "adelante"

        elif tipo == "GIRAR":
            angulo = re.search(r"(-?\d+(?:[.,]\d+)?)\s*(?:grados?|°)", normalizado)
            angulo_palabras = _numero_antes_de_unidad(
                normalizado, ("grado", "grados")
            )
            if angulo:
                numero = float(angulo.group(1).replace(",", "."))
                parametros["angulo_deg"] = int(numero) if numero.is_integer() else numero
            elif angulo_palabras is not None:
                parametros["angulo_deg"] = angulo_palabras
            elif "media vuelta" in normalizado:
                parametros["angulo_deg"] = 180
            elif re.search(r"\bgrados?\b", normalizado):
                parametros["_parametro_incierto"] = "angulo no reconocido"

            if "derecha" in normalizado:
                parametros["direccion"] = "derecha"
            elif "izquierda" in normalizado:
                parametros["direccion"] = "izquierda"
            else:
                parametros["direccion"] = "izquierda"

        elif tipo == "EJECUTAR_EMOTE":
            emote = resolver_emote(normalizado)
            if emote is None:
                parametros["_parametro_incierto"] = "emote no reconocido"
            else:
                parametros["emote"] = emote

        elif tipo == "CONTAR_CHISTE":
            emote = resolver_emote(normalizado)
            if emote is not None:
                parametros["emote_solicitado"] = emote

        return parametros


# =====================================================================
#  ETAPA 3 - VALIDADOR DE SEGURIDAD
# =====================================================================
class ValidadorSeguridad:
    """La ultima barrera antes del robot.

    Este es el corazon del TP. Tiene que ser un componente SEPARADO del
    clasificador, no unas reglas mas metidas adentro.

    El motivo: tu clasificador se va a equivocar. Todos se equivocan. Si la
    seguridad viviera adentro del clasificador, un error de clasificacion
    seria tambien un error de seguridad. Separandolos, un error de
    clasificacion sigue siendo bloqueado.
    """

    # Palabras que describen acciones que el robot no debe intentar nunca.
    PALABRAS_PELIGROSAS = ("salta", "salto", "corre", "corré", "sprint",
                           "empuja", "empujá", "golpea", "rompe", "tira",
                           "cae", "fuerza")
    DISTANCIA_MAX_M = 5.0

    def __init__(self, perfil):
        # perfil trae los limites de tu materia:
        #   perfil.velocidad_max          m/s
        #   perfil.velocidad_angular_max  rad/s
        #   perfil.duracion_max           segundos por orden
        #   perfil.bateria_min            porcentaje
        self.perfil = perfil

    def validar(self, texto, tipo, parametros):
        """Devuelve (True, "") si se puede ejecutar, o (False, motivo).

        Que conviene revisar:

          1. Palabras peligrosas en el TEXTO ORIGINAL. Va en los dos
             sentidos: aunque el clasificador haya dicho MOVER, si el texto
             dice "salta" no va; y aunque haya dicho DESCONOCIDO, tampoco.
             Por eso mirás el texto y no solo la intencion.
          2. Velocidad pedida por encima de perfil.velocidad_max.
          3. Distancia que no tenga sentido (100 metros en un aula, no).
          4. Angulo mayor a 180 grados.
          5. Cualquier cosa que no puedas justificar como segura.

        Cuando bloquees, devolve un motivo entendible: va al reporte.
        """
        normalizado = _normalizar(texto)
        if normalizado.startswith("[voz no confirmada]"):
            return False, "[VOZ NO CONFIRMADA] No ejecuto ninguna accion."
        peligrosas = {_normalizar(p) for p in self.PALABRAS_PELIGROSAS}
        palabras = set(re.findall(r"\b\w+\b", normalizado))
        encontradas = sorted(palabras & peligrosas)
        if encontradas:
            return False, f"palabra peligrosa: {encontradas[0]}"
        for patron in (
            r"\bsalt(?:ar|a|e|en|amos)\b",
            r"\bcorr(?:er|e|an|amos)\b",
            r"\bempuj(?:ar|a|e|en|amos)\b",
            r"\bgolpe(?:ar|a|e|en|amos)\b",
            r"\bromp(?:er|e|an|amos)\b",
            r"\bcae(?:r|te|n)?\b",
        ):
            coincidencia = re.search(patron, normalizado)
            if coincidencia:
                return False, f"palabra peligrosa: {coincidencia.group(0)}"
        if parametros.get("_parametro_incierto"):
            return False, str(parametros["_parametro_incierto"])

        try:
            if "distancia_m" in parametros:
                distancia = _numero_finito(parametros["distancia_m"], "distancia")
                if distancia <= 0:
                    return False, "la distancia debe ser mayor que cero"
                if distancia > self.DISTANCIA_MAX_M:
                    return False, f"distancia > maximo seguro ({self.DISTANCIA_MAX_M:g} m)"

            if "angulo_deg" in parametros:
                angulo = _numero_finito(parametros["angulo_deg"], "angulo")
                if angulo <= 0:
                    return False, "el angulo debe ser mayor que cero"
                if angulo > 180:
                    return False, "angulo > 180 grados"

            if "velocidad_ms" in parametros:
                velocidad = _numero_finito(parametros["velocidad_ms"], "velocidad")
                if velocidad <= 0:
                    return False, "la velocidad debe ser mayor que cero"
                if velocidad > self.perfil.velocidad_max + 1e-9:
                    return False, f"velocidad > maximo ({self.perfil.velocidad_max:g} m/s)"

            if "velocidad_giro" in parametros:
                velocidad_giro = _numero_finito(parametros["velocidad_giro"], "velocidad de giro")
                if velocidad_giro <= 0:
                    return False, "la velocidad de giro debe ser mayor que cero"
                if velocidad_giro > self.perfil.velocidad_angular_max + 1e-9:
                    return False, (
                        "velocidad de giro > maximo "
                        f"({self.perfil.velocidad_angular_max:g} rad/s)"
                    )
        except (TypeError, ValueError) as exc:
            return False, str(exc)

        return True, ""

    def validar_estado_robot(self, robot, tipo):
        """Valida telemetria antes de locomocion o gesto fisico."""

        if robot is None or tipo not in (
            "MOVER", "GIRAR", "SALUDO", "EJECUTAR_EMOTE",
        ):
            return True, ""
        try:
            estado = robot.verificar_estado()
        except Exception as exc:
            return False, f"no se pudo verificar el estado del robot: {exc}"
        bateria = estado.get("bateria") if isinstance(estado, dict) else getattr(
            estado, "bateria", None
        )
        if bateria is None:
            return False, "bateria desconocida: la accion fisica queda bloqueada"
        try:
            nivel = int(float(bateria))
        except (TypeError, ValueError):
            return False, "nivel de bateria invalido"
        if nivel < self.perfil.bateria_min:
            return False, (
                f"bateria {nivel}% menor al minimo {self.perfil.bateria_min}%"
            )
        return True, ""


# =====================================================================
#  EL AGENTE - une las tres etapas y llama al ejecutor
# =====================================================================
class AgenteRobot:
    FACTOR_MODO_LENTO = 0.5

    def __init__(
        self,
        robot=None,
        capacidades=None,
        tts=None,
        usar_tts_local=False,
        rng=None,
        al_terminar_chiste=None,
        salida_tts=print,
        emote_manager=None,
        rng_emotes=None,
        salida_emotes=print,
    ):
        self.robot = robot
        self.capacidades = capacidades or detectar_capacidades(robot)
        self.clasificador = ClasificadorIntencion()
        self.extractor = ExtractorParametros()
        self.validador = ValidadorSeguridad(
            robot.perfil if robot else _perfil_por_defecto())
        self.ejecutor = Ejecutor(robot) if robot else None
        self.estado = EstadoAgente()
        # Alias compatible con el esqueleto original y practico para el informe.
        self.historial = self.estado.historial
        self.bolsa_chistes = BolsaChistes(rng)
        consola = TTSConsola(salida_tts)
        self.tts = (
            TTSConFallback(tts, consola)
            if tts is not None
            else crear_tts(
                self.capacidades, usar_local=usar_tts_local, salida=salida_tts
            )
        )
        self.emotes = emote_manager or crear_emote_manager(
            self.capacidades,
            robot=robot,
            rng=rng_emotes,
            hablar=self.tts.hablar,
            salida=salida_emotes,
        )
        self.al_terminar_chiste = (
            al_terminar_chiste or self.emotes.ejecutar_aleatorio
        )

    @property
    def modo_lento(self):
        return self.estado.modo_lento

    @property
    def ultima_accion_ejecutada(self):
        return self.estado.ultima_accion_ejecutada

    @property
    def ultimo_movimiento_reversible(self):
        return self.estado.ultimo_movimiento_reversible

    def procesar(self, texto):
        """El pipeline completo. ESTA ES LA FUNCION QUE SE TE EVALUA.

        Tiene que devolver un diccionario con esta forma:

            {
              "tipo": "MOVER",          uno de los seis tipos
              "parametros": {...},      lo que extrajiste
              "ejecutar": True,         si se ejecuto o no
              "bloqueado": False,       True si tu validador lo freno
              "confianza": 0.9,
              "texto_original": texto,
              "mensaje": "...",         que paso, en castellano
            }

        Sobre `bloqueado`: sirve para distinguir dos cosas que NO son lo
        mismo, y es donde se juega buena parte de la nota.

            DESCONOCIDO   no entendiste, y no habia nada peligroso
                          ("hola, como estas?")
            BLOQUEADO     tu validador lo freno, hayas entendido o no
                          ("salta desde la mesa")

        Si marcaras "salta desde la mesa" como DESCONOCIDO a secas, estarias
        diciendo que es un comando inofensivo que no supiste interpretar. Y
        es al reves: es el que MAS importa frenar.
        """
        texto = "" if texto is None else str(texto).strip()
        tipo = self.clasificador.clasificar(texto)
        parametros = self.extractor.extraer(texto, tipo)

        # El validador corre siempre, incluso para DESCONOCIDO y metacomandos.
        seguro, motivo = self.validador.validar(texto, tipo, parametros)
        if not seguro:
            return self._finalizar(tipo, parametros, texto, False, True, 1.0, motivo)

        if tipo == "DESCONOCIDO":
            return self._finalizar(
                tipo, parametros, texto, False, False, 0.0,
                "no reconoci una orden segura del dominio",
            )

        if tipo == "AYUDA":
            return self._finalizar(
                tipo, {}, texto, True, False, 1.0, AYUDA_BREVE,
            )

        if tipo == "MODO_LENTO":
            self.estado.modo_lento = True
            return self._finalizar(tipo, {}, texto, True, False, 1.0, "modo lento activado")

        if tipo == "MODO_NORMAL":
            self.estado.modo_lento = False
            return self._finalizar(tipo, {}, texto, True, False, 1.0, "modo normal activado")

        if tipo == "REPETIR_ULTIMA_ACCION":
            anterior = self.estado.ultima_accion_ejecutada
            if anterior is None:
                return self._finalizar(
                    tipo, {}, texto, False, False, 1.0,
                    "no hay una accion anterior para repetir",
                )
            return self._ejecutar_accion(anterior.copia(), texto, "repeticion")

        if tipo == "REVERSA":
            movimiento = self.estado.ultimo_movimiento_reversible
            if movimiento is None:
                return self._finalizar(
                    tipo, {}, texto, False, False, 1.0,
                    "no hay un movimiento anterior para revertir",
                )
            inversa = invertir_movimiento(movimiento)
            return self._ejecutar_accion(inversa, texto, "reversa aproximada")

        if tipo == "CONTAR_CHISTE":
            parametros = dict(parametros)
            parametros["chiste"] = self.bolsa_chistes.siguiente()
        if tipo == "DETENERSE" and (
            self.estado.tts_activo or getattr(self.emotes, "activo", None)
        ):
            self.tts.detener()
            self.emotes.cancelar()
        accion = AccionUsuario(tipo, dict(parametros), texto)
        return self._ejecutar_accion(accion, texto)

    def _ejecutar_accion(self, accion, texto_solicitud, contexto=""):
        """Revalida y ejecuta una copia semantica bajo el estado actual."""

        parametros_semanticos = dict(accion.parametros)
        seguro, motivo = self.validador.validar(
            accion.texto_original, accion.tipo, parametros_semanticos,
        )
        if not seguro:
            prefijo = f"{contexto} bloqueada" if contexto else "accion bloqueada"
            return self._finalizar(
                accion.tipo, parametros_semanticos, texto_solicitud,
                False, True, 1.0, f"{prefijo}: {motivo}",
            )

        efectivos = self._aplicar_modo(parametros_semanticos, accion.tipo)
        # La transformacion de modo lento tambien pasa por la barrera final.
        seguro, motivo = self.validador.validar(accion.texto_original, accion.tipo, efectivos)
        if not seguro:
            return self._finalizar(
                accion.tipo, efectivos, texto_solicitud, False, True, 1.0, motivo,
            )

        seguro, motivo = self.validador.validar_estado_robot(self.robot, accion.tipo)
        if not seguro:
            return self._finalizar(
                accion.tipo, efectivos, texto_solicitud, False, True, 1.0, motivo,
            )

        destino = getattr(self.robot, "destino", None) if self.robot is not None else None
        if (
            destino not in (None, "simulador")
            and accion.tipo in ("MOVER", "GIRAR", "SALUDO", "EJECUTAR_EMOTE")
            and not self.capacidades.telemetria_bateria_confirmada
        ):
            return self._finalizar(
                accion.tipo, efectivos, texto_solicitud, False, True, 1.0,
                "telemetria de bateria real no confirmada: accion fisica bloqueada",
            )

        if accion.tipo == "CONTAR_CHISTE":
            chiste = str(parametros_semanticos["chiste"])
            self.estado.tts_activo = True
            try:
                self.tts.hablar(chiste)
            except Exception:
                # Una implementacion externa defectuosa tampoco debe tumbar al agente.
                TTSConsola().hablar(chiste)
            finally:
                self.estado.tts_activo = False
            elegido = None
            solicitado = parametros_semanticos.get("emote_solicitado")
            try:
                if solicitado is not None:
                    if self.emotes.ejecutar(str(solicitado)):
                        elegido = str(solicitado)
                else:
                    elegido = self.al_terminar_chiste(chiste)
            except Exception:
                elegido = None
            if elegido:
                parametros_semanticos["emote"] = elegido
                efectivos["emote"] = elegido
                mensaje = f"chiste contado; emote {elegido}"
            else:
                mensaje = "chiste contado; no había un emote habilitado"
        elif accion.tipo == "EJECUTAR_EMOTE":
            nombre = str(parametros_semanticos["emote"])
            if not self.emotes.ejecutar(nombre):
                return self._finalizar(
                    accion.tipo, efectivos, texto_solicitud, False, True, 1.0,
                    f"emote {nombre} no disponible para este destino",
                )
            mensaje = f"emote {nombre} iniciado"
        elif self.ejecutor is None:
            mensaje = "accion validada (modo sin robot)"
        else:
            try:
                mensaje = str(self.ejecutor.ejecutar(accion.tipo, efectivos))
            except Exception as exc:
                self._detener_robot_seguro()
                return self._finalizar(
                    accion.tipo, efectivos, texto_solicitud, False, True, 1.0,
                    f"fallo de ejecucion; robot detenido: {exc}",
                )
            if mensaje.startswith("RECHAZADO POR EL ROBOT"):
                self._detener_robot_seguro()
                return self._finalizar(
                    accion.tipo, efectivos, texto_solicitud, False, True, 1.0, mensaje,
                )

        self.estado.registrar_ejecucion(accion)
        if contexto:
            mensaje = f"{contexto}: {mensaje}"
        return self._finalizar(
            accion.tipo, efectivos, texto_solicitud, True, False, 1.0, mensaje,
        )

    def _aplicar_modo(self, parametros, tipo):
        efectivos = dict(parametros)
        if not self.estado.modo_lento:
            return efectivos
        if tipo == "MOVER":
            base = float(efectivos.get("velocidad_ms", self.validador.perfil.velocidad_max))
            efectivos["velocidad_ms"] = min(
                base * self.FACTOR_MODO_LENTO,
                self.validador.perfil.velocidad_max,
            )
        elif tipo == "GIRAR":
            base = float(
                efectivos.get("velocidad_giro", self.validador.perfil.velocidad_angular_max)
            )
            efectivos["velocidad_giro"] = min(
                base * self.FACTOR_MODO_LENTO,
                self.validador.perfil.velocidad_angular_max,
            )
        return efectivos

    def _finalizar(self, tipo, parametros, texto, ejecutar, bloqueado, confianza, mensaje):
        resultado = {
            "tipo": tipo,
            "parametros": dict(parametros),
            "ejecutar": bool(ejecutar),
            "bloqueado": bool(bloqueado),
            "confianza": float(confianza),
            "texto_original": texto,
            "mensaje": mensaje,
        }
        self.estado.registrar_resultado(resultado)
        return resultado

    def _detener_robot_seguro(self):
        if self.robot is None:
            return
        try:
            self.robot.detenerse()
        except Exception:
            pass


def _normalizar(texto):
    texto = "" if texto is None else str(texto).lower()
    return "".join(
        caracter for caracter in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caracter) != "Mn"
    )


def _numero_finito(valor, nombre):
    numero = float(valor)
    if not math.isfinite(numero):
        raise ValueError(f"{nombre} debe ser un numero finito")
    return numero


_UNIDADES_ES = {
    "cero": 0, "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3,
    "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9,
}
_ESPECIALES_ES = {
    "diez": 10, "once": 11, "doce": 12, "trece": 13, "catorce": 14,
    "quince": 15, "dieciseis": 16, "diecisiete": 17, "dieciocho": 18,
    "diecinueve": 19, "veinte": 20, "veintiuno": 21, "veintidos": 22,
    "veintitres": 23, "veinticuatro": 24, "veinticinco": 25,
    "veintiseis": 26, "veintisiete": 27, "veintiocho": 28, "veintinueve": 29,
}
_DECENAS_ES = {
    "treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60,
    "setenta": 70, "ochenta": 80, "noventa": 90,
}
_CENTENAS_ES = {
    "cien": 100, "ciento": 100, "doscientos": 200, "doscientas": 200,
    "trescientos": 300, "trescientas": 300, "cuatrocientos": 400,
    "cuatrocientas": 400, "quinientos": 500, "quinientas": 500,
    "seiscientos": 600, "seiscientas": 600, "setecientos": 700,
    "setecientas": 700, "ochocientos": 800, "ochocientas": 800,
    "novecientos": 900, "novecientas": 900,
}


def _parsear_numero_es(palabras):
    if palabras in (("medio",), ("media",)):
        return 0.5
    tokens = [p for p in palabras if p != "y"]
    if not tokens or len(tokens) > 3:
        return None
    if tokens == ["mil"]:
        return 1000
    total = 0
    if tokens and tokens[0] in _CENTENAS_ES:
        total += _CENTENAS_ES[tokens.pop(0)]
    if not tokens:
        return total
    if len(tokens) == 1:
        palabra = tokens[0]
        if palabra in _ESPECIALES_ES:
            return total + _ESPECIALES_ES[palabra]
        if palabra in _DECENAS_ES:
            return total + _DECENAS_ES[palabra]
        if palabra in _UNIDADES_ES:
            return total + _UNIDADES_ES[palabra]
        return None
    if len(tokens) == 2 and tokens[0] in _DECENAS_ES and tokens[1] in _UNIDADES_ES:
        return total + _DECENAS_ES[tokens[0]] + _UNIDADES_ES[tokens[1]]
    return None


def _numero_antes_de_unidad(texto, unidades, excluir_velocidad=False):
    tokens = re.findall(r"\b\w+\b", texto)
    for indice, token in enumerate(tokens):
        if token not in unidades:
            continue
        if excluir_velocidad and tokens[indice + 1:indice + 3] == ["por", "segundo"]:
            continue
        for inicio in range(max(0, indice - 4), indice):
            numero = _parsear_numero_es(tuple(tokens[inicio:indice]))
            if numero is not None:
                return numero
    return None


def _numero_antes_de_frase(texto, frases):
    tokens = re.findall(r"\b\w+\b", texto)
    for frase in frases:
        largo = len(frase)
        for indice in range(len(tokens) - largo + 1):
            if tuple(tokens[indice:indice + largo]) != frase:
                continue
            for inicio in range(max(0, indice - 4), indice):
                numero = _parsear_numero_es(tuple(tokens[inicio:indice]))
                if numero is not None:
                    return numero
    return None


def _perfil_por_defecto():
    """Permite evaluar el agente sin abrir el simulador."""
    import sys
    from pathlib import Path
    entorno = Path(__file__).resolve().parent.parent / "entorno"
    if str(entorno) not in sys.path:
        sys.path.insert(0, str(entorno))
    from sim.safety import perfil
    return perfil("tp07")


# =====================================================================
#  PROGRAMA PRINCIPAL
# =====================================================================
def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Agente TP07 por texto o voz local")
    parser.add_argument(
        "--sin-robot", action="store_true",
        help="abre el modo interactivo sin conectarse a un robot",
    )
    parser.add_argument(
        "--evaluar", action="store_true",
        help="ejecuta explícitamente los 25 casos y termina",
    )
    parser.add_argument("--voz", action="store_true", help="usa el microfono como entrada")
    parser.add_argument("--list-mics", action="store_true", help="lista microfonos y termina")
    parser.add_argument("--mic", type=int, default=None, help="indice de microfono")
    parser.add_argument("--stt-profile", choices=("quality", "light"), default="quality")
    parser.add_argument("--stt-device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument(
        "--tts", choices=("console", "local"), default="local",
        help="salida de voz; local usa pyttsx3 offline (predeterminado)",
    )
    args = parser.parse_args(argv)

    if args.list_mics:
        from voz import CapturadorMicrofono, ErrorVoz
        try:
            dispositivos = CapturadorMicrofono().listar_microfonos()
        except ErrorVoz as exc:
            print(f"No se pudieron listar microfonos: {exc}")
            return 1
        if not dispositivos:
            print("No se encontraron microfonos de entrada.")
        for d in dispositivos:
            print(
                f"{d.indice}: {d.nombre} "
                f"({d.canales_entrada} canales, {d.frecuencia_predeterminada:g} Hz)"
            )
        return 0

    robot = None
    try:
        # La evaluación es deliberadamente offline: nunca debe mover un robot.
        if not args.sin_robot and not args.evaluar:
            robot = Robot()
            robot.conectar()
            # Es la única orden permitida durante el arranque normal.
            robot.detenerse()

        agente = AgenteRobot(robot, usar_tts_local=args.tts == "local")
        if args.evaluar:
            from evaluar import evaluar

            evaluar(agente)
            return 0

        if args.voz:
            _bucle_voz(agente, args.stt_profile, args.stt_device, args.mic)
        else:
            _bucle_texto(agente)
    finally:
        if robot is not None:
            robot.desconectar()
    return 0


def _bucle_texto(agente):
    print("\n=== AGENTE G1 ===")
    print("Listo. Esperando orden.")
    print('Ejemplos: "avanzá 1 metro", "baile", "emote 4", "contame un chiste".')
    while True:
        try:
            texto = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not texto:
            break
        resultado = agente.procesar(texto)
        print(f"{resultado['tipo']}  {resultado.get('mensaje', '')}")


def _bucle_voz(agente, perfil, dispositivo_stt, microfono):
    from voz import ErrorVoz, ReconocedorVozLocal, procesar_una_orden_por_voz

    reconocedor = ReconocedorVozLocal(perfil, dispositivo_stt)
    print("\n  Modo voz local. Ctrl+C para salir.")
    print("  Guarda silencio un segundo para calibrar el ruido ambiente...")
    try:
        umbral = reconocedor.calibrar(microfono)
        print(f"  Microfono calibrado (umbral RMS {umbral:.4f}).")
        while True:
            print("\n  Escuchando...")
            try:
                resultado = procesar_una_orden_por_voz(agente, reconocedor, microfono)
                print(f"    Oi: {resultado.get('transcripcion_original', '')}")
                print(f"    {resultado['tipo']}  {resultado.get('mensaje', '')}")
            except ErrorVoz as exc:
                print(f"    [VOZ] {exc}")
    except KeyboardInterrupt:
        print("\n  Modo voz finalizado.")
    except ErrorVoz as exc:
        print(f"  No se pudo iniciar voz: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
