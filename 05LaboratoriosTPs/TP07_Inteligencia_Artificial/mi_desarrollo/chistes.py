"""Banco cerrado de 100 chistes y bolsa aleatoria sin repeticion."""

from __future__ import annotations

import random
from typing import MutableSequence


CHISTES: tuple[str, ...] = (
    # 1-10
    "¿Por qué el libro de matemáticas estaba triste? Porque tenía muchos problemas.",
    "¿Qué hace un pez? ¡Nada!",
    "¿Cómo se llama el primo vegetariano de Bruce Lee? Broco Lee.",
    "¿Qué le dijo un techo a otro? Techo de menos.",
    "¿Qué hace una abeja en el gimnasio? ¡Zum-ba!",
    "¿Cuál es el café más peligroso? El ex-preso.",
    "¿Qué le dijo una pared a la otra? Nos vemos en la esquina.",
    "¿Cómo se despiden los químicos? Ácido un placer.",
    "¿Qué hace una vaca con los ojos cerrados? Leche concentrada.",
    "¿Por qué el tomate se sonrojó? Porque vio la ensalada.",
    # 11-20
    "¿Qué le dijo el cero al ocho? Bonito cinturón.",
    "¿Cuál es el colmo de un jardinero? Que siempre lo dejen plantado.",
    "¿Cómo se llama un boomerang que no vuelve? Palo.",
    "¿Por qué la computadora fue al médico? Porque tenía un virus.",
    "¿Qué hace una nube con picazón? Se rasca-cielo.",
    "¿Qué le dijo el mar a la playa? Nada, solo hizo olas.",
    "¿Cuál es el animal más antiguo? La cebra, porque está en blanco y negro.",
    "¿Cómo queda un mago después de comer? Magordito.",
    "¿Qué hace un perro con un taladro? Taladrando.",
    "¿Qué le dijo una impresora a otra? ¿Esa hoja es tuya o es impresión mía?",
    # 21-30
    "¿Cuál es el último animal que subió al arca? El del-fin.",
    "¿Cómo se llama el campeón de buceo japonés? Tokofondo.",
    "¿Y el subcampeón de buceo? Kasitoko.",
    "¿Qué hace una caja en el gimnasio? Caja fuerte.",
    "¿Por qué el reloj fue al psicólogo? Porque perdió la noción del tiempo.",
    "¿Qué le dijo un semáforo a otro? No me mires, me estoy cambiando.",
    "¿Cómo se llama un cinturón hecho de relojes? Una pérdida de tiempo.",
    "¿Qué hace una escoba contenta? Barre de alegría.",
    "¿Por qué la bicicleta no podía mantenerse de pie? Porque estaba cansada.",
    "¿Cuál es el colmo de un electricista? No encontrar su corriente de trabajo.",
    # 31-40
    "¿Qué le dijo el lápiz al papel? Tenés buena impresión.",
    "¿Por qué el calendario está feliz? Porque sus días están contados.",
    "¿Qué hace un limón en una fiesta? Se pone de jugo.",
    "¿Cómo saluda un panadero? Harina verte.",
    "¿Qué le dijo una uva verde a una morada? ¡Respirá!",
    "¿Por qué los pájaros no usan redes sociales? Porque ya tienen Twitter.",
    "¿Qué instrumento toca una serpiente? La cobra-tía.",
    "¿Cómo se llama el hermano limpio de Harry Potter? Harry Potable.",
    "¿Qué hace un caracol sobre una tortuga? Va a toda velocidad.",
    "¿Qué le dijo el Wi-Fi al router? Siento una conexión entre nosotros.",
    # 41-50
    "¿Por qué el músico llevó una escalera? Para alcanzar las notas altas.",
    "¿Qué le dijo una taza a otra? ¿Qué taza-ciendo?",
    "¿Cuál es el colmo de un fotógrafo? Que todo se le revele.",
    "¿Qué hace una pelota cuando está aburrida? Da vueltas al asunto.",
    "¿Cómo se llama un oso sin dientes? Oso gomoso.",
    "¿Por qué el pan fue al banco? Porque necesitaba más masa.",
    "¿Qué le dijo el uno al diez? Para ser como yo, tenés que ser sincero.",
    "¿Qué hace una pila en el recreo? Se carga de energía.",
    "¿Por qué el diccionario sabe tanto? Porque tiene todas las palabras.",
    "¿Qué hace un árbol en Internet? Se conecta a la raíz.",
    # 51-60
    "¿Cómo se llama el campeón de escondidas? Nadie lo sabe.",
    "¿Por qué el celular llevó paraguas? Porque había llamadas perdidas.",
    "¿Qué le dijo la luna al sol? Tan grande y no te dejan salir de noche.",
    "¿Cuál es el colmo de una silla? Tener cuatro patas y no poder caminar.",
    "¿Qué hace un botón en una escuela? Aprende a abrochar ideas.",
    "¿Por qué el helado estudió música? Quería aprender las escalas.",
    "¿Qué le dijo el tenedor a la cuchara? No revuelvas el tema.",
    "¿Cómo se llama un gato que programa? Código Miau.",
    "¿Qué hace una regla cuando se aburre? Mide el tiempo.",
    "¿Por qué la naranja usa protector solar? Porque tiene mucha pulpa sensible.",
    # 61-70
    "¿Qué le dijo el teclado al mouse? Vos sí que sabés hacer clic conmigo.",
    "¿Cuál es el colmo de un astronauta? Estar siempre en las nubes.",
    "¿Qué hace una lámpara cuando tiene una idea? Se ilumina.",
    "¿Cómo se llama una oveja que canta? Lana del Rey.",
    "¿Por qué el cuaderno fue de viaje? Para conocer nuevas hojas.",
    "¿Qué le dijo el hielo al vaso? Me derrito por vos.",
    "¿Qué hace una galletita en la computadora? Borra las cookies.",
    "¿Cómo se llama un dinosaurio dormido? Dino-ronquido.",
    "¿Por qué el lápiz sacó buena nota? Porque tenía buena punta.",
    "¿Qué le dijo una puerta a otra? Te veo a la salida.",
    # 71-80
    "¿Qué hace un robot en vacaciones? Recarga las baterías.",
    "¿Cuál es el colmo de un panadero? No saber cómo ganarse el pan.",
    "¿Qué le dijo el café al azúcar? Sin vos mi vida es amarga.",
    "¿Por qué el mapa nunca se pierde? Porque conoce todos los caminos.",
    "¿Qué hace una estrella en clase? Brilla por su participación.",
    "¿Cómo se llama un pato detective? Sherlock Cuac.",
    "¿Por qué la almohada es buena consejera? Porque consulta todo con la cabeza.",
    "¿Qué le dijo el verano al invierno? Nos vemos en seis meses.",
    "¿Qué hace una foto en el gimnasio? Se pone en forma.",
    "¿Cuál es el colmo de un zapatero? Que siempre le sigan los pasos.",
    # 81-90
    "¿Por qué el río nunca se apura? Porque sigue su corriente.",
    "¿Qué le dijo el ascensor al edificio? Estoy subiendo en la vida.",
    "¿Cómo se llama un conejo que cuenta chistes? Risitas de la suerte.",
    "¿Qué hace una tecla en el mar? Navega con control.",
    "¿Por qué el espejo aprobó el examen? Porque reflejó muy bien.",
    "¿Qué le dijo la sal a la pimienta? Juntas le damos sabor al día.",
    "¿Cómo se llama un pez que manda mensajes? Pez-tanea.",
    "¿Por qué la sopa fue a la escuela? Para aprender el abecaldo.",
    "¿Qué hace un tornillo en una charla? Da muchas vueltas.",
    "¿Cuál es el colmo de un meteorólogo? No tener tiempo para nada.",
    # 91-100
    "¿Qué le dijo una bombilla a otra? Me alegrás el día.",
    "¿Por qué la mochila estaba orgullosa? Porque cargaba con sus logros.",
    "¿Cómo se llama una vaca que sabe música? Muuu-sical.",
    "¿Qué hace un lápiz en una carrera? Saca punta.",
    "¿Por qué el queso sonrió? Porque le dijeron algo muy gouda.",
    "¿Qué le dijo el papel al sobre? Guardá el secreto.",
    "¿Cómo se llama un perro que hace magia? Labracadabrador.",
    "¿Por qué la computadora tenía frío? Porque dejó Windows abierto.",
    "¿Qué hace un tomate con capa? Es un súper alimento.",
    "¿Cuál es el colmo de un robot? Tener los nervios de acero.",
)


class BolsaChistes:
    """Entrega todos los chistes una vez antes de iniciar otra ronda."""

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()
        self._bolsa: list[str] = []
        self._ultimo: str | None = None

    def siguiente(self) -> str:
        if not self._bolsa:
            self._rellenar()
        chiste = self._bolsa.pop()
        self._ultimo = chiste
        return chiste

    def _rellenar(self) -> None:
        nueva: MutableSequence[str] = list(CHISTES)
        self.rng.shuffle(nueva)
        # pop() consume desde el final: esa es la frontera entre rondas.
        if self._ultimo is not None and nueva[-1] == self._ultimo:
            nueva[-1], nueva[0] = nueva[0], nueva[-1]
        self._bolsa = list(nueva)

