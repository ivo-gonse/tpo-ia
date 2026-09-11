"""Animaciones cinematicas de emotes para el G1 de MuJoCo.

Esta capa conoce nombres de joints del ``g1_29dof.xml`` y los resuelve contra
el ``MjModel`` compilado. Nunca usa indices hardcodeados y nunca se importa
desde el backend del robot real.

Las manos del modelo incluido son mallas rigidas ``*_rubber_hand``: no hay
joints de dedos ni de pulgar. Por eso PULGAR_ARRIBA y FINGER_GUNS usan una
aproximacion de brazo y muneca.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping


@dataclass(frozen=True)
class Fotograma:
    progreso: float
    pose: Mapping[str, float]


@dataclass(frozen=True)
class Animacion:
    duracion: float
    fotogramas: tuple[Fotograma, ...]


# Son los unicos joints que una animacion de emote puede escribir. Las piernas
# y el floating_base_joint quedan fuera deliberadamente.
JOINTS_SUPERIORES = frozenset(
    {
        "waist_yaw_joint",
        "waist_roll_joint",
        "waist_pitch_joint",
        "left_shoulder_pitch_joint",
        "left_shoulder_roll_joint",
        "left_shoulder_yaw_joint",
        "left_elbow_joint",
        "left_wrist_roll_joint",
        "left_wrist_pitch_joint",
        "left_wrist_yaw_joint",
        "right_shoulder_pitch_joint",
        "right_shoulder_roll_joint",
        "right_shoulder_yaw_joint",
        "right_elbow_joint",
        "right_wrist_roll_joint",
        "right_wrist_pitch_joint",
        "right_wrist_yaw_joint",
    }
)

# Pose neutral que el visor ya usa para el G1 (robots.py), expresada por
# nombre para poder verificar las velocidades sin depender de indices.
POSE_NEUTRAL_G1 = {
    "left_shoulder_pitch_joint": 0.20,
    "left_elbow_joint": -0.30,
    "right_shoulder_pitch_joint": 0.20,
    "right_elbow_joint": -0.30,
}
VELOCIDAD_VISUAL_MAX_RAD_S = 5.2


def _f(progreso: float, **pose: float) -> Fotograma:
    return Fotograma(progreso, pose)


_RISA_A = {
    "waist_pitch_joint": -0.10,
    "waist_roll_joint": 0.06,
    "waist_yaw_joint": -0.06,
    "left_shoulder_pitch_joint": -0.90,
    "left_shoulder_roll_joint": 0.30,
    "left_shoulder_yaw_joint": -0.12,
    "left_elbow_joint": 1.25,
    "left_wrist_roll_joint": -0.22,
    "left_wrist_pitch_joint": -0.25,
    "right_shoulder_pitch_joint": -0.90,
    "right_shoulder_roll_joint": -0.30,
    "right_shoulder_yaw_joint": 0.12,
    "right_elbow_joint": 1.25,
    "right_wrist_roll_joint": 0.22,
    "right_wrist_pitch_joint": -0.25,
}
_RISA_B = {
    "waist_pitch_joint": 0.08,
    "waist_roll_joint": -0.06,
    "waist_yaw_joint": 0.06,
    "left_shoulder_pitch_joint": -1.05,
    "left_shoulder_roll_joint": 0.24,
    "left_shoulder_yaw_joint": 0.08,
    "left_elbow_joint": 1.42,
    "left_wrist_roll_joint": 0.18,
    "left_wrist_pitch_joint": 0.10,
    "right_shoulder_pitch_joint": -1.05,
    "right_shoulder_roll_joint": -0.24,
    "right_shoulder_yaw_joint": -0.08,
    "right_elbow_joint": 1.42,
    "right_wrist_roll_joint": -0.18,
    "right_wrist_pitch_joint": 0.10,
}

_BAILE_IZQUIERDA = {
    "waist_yaw_joint": -0.28,
    "waist_roll_joint": 0.10,
    "left_shoulder_pitch_joint": -2.25,
    "left_shoulder_roll_joint": 0.38,
    "left_elbow_joint": -0.20,
    "left_wrist_roll_joint": 0.45,
    "right_shoulder_pitch_joint": -0.65,
    "right_shoulder_roll_joint": -0.15,
    "right_elbow_joint": 1.20,
    "right_wrist_yaw_joint": 0.50,
}
_BAILE_DERECHA = {
    "waist_yaw_joint": 0.28,
    "waist_roll_joint": -0.10,
    "left_shoulder_pitch_joint": -0.65,
    "left_shoulder_roll_joint": 0.15,
    "left_elbow_joint": 1.20,
    "left_wrist_yaw_joint": -0.50,
    "right_shoulder_pitch_joint": -2.25,
    "right_shoulder_roll_joint": -0.38,
    "right_elbow_joint": -0.20,
    "right_wrist_roll_joint": -0.45,
}

_BRAZOS_ABIERTOS_TRANSICION = {
    "left_shoulder_pitch_joint": -1.20,
    "left_shoulder_roll_joint": 0.65,
    "left_shoulder_yaw_joint": 0.0,
    "left_elbow_joint": 0.0,
    "right_shoulder_pitch_joint": -1.20,
    "right_shoulder_roll_joint": -0.65,
    "right_shoulder_yaw_joint": 0.0,
    "right_elbow_joint": 0.0,
}
_BRAZOS_CRUZADOS = {
    "waist_yaw_joint": 0.24,
    # Los antebrazos quedan escalonados, cruzados frente al pecho y sin
    # penetrarse entre sí en el modelo de colisión incluido.
    "left_shoulder_pitch_joint": -1.272,
    "left_shoulder_roll_joint": 0.132,
    "left_shoulder_yaw_joint": -1.248,
    "left_elbow_joint": -0.291,
    "right_shoulder_pitch_joint": -1.155,
    "right_shoulder_roll_joint": -0.268,
    "right_shoulder_yaw_joint": 1.528,
    "right_elbow_joint": -0.109,
}
_BRAZO_DERECHO_CRUZADO = {
    **_BRAZOS_ABIERTOS_TRANSICION,
    "waist_yaw_joint": _BRAZOS_CRUZADOS["waist_yaw_joint"],
    "right_shoulder_pitch_joint": _BRAZOS_CRUZADOS[
        "right_shoulder_pitch_joint"
    ],
    "right_shoulder_roll_joint": _BRAZOS_CRUZADOS[
        "right_shoulder_roll_joint"
    ],
    "right_shoulder_yaw_joint": _BRAZOS_CRUZADOS[
        "right_shoulder_yaw_joint"
    ],
    "right_elbow_joint": _BRAZOS_CRUZADOS["right_elbow_joint"],
}

_PULGAR_ARRIBA_APROX = {
    "waist_yaw_joint": -0.14,
    "waist_roll_joint": -0.04,
    "right_shoulder_pitch_joint": -0.735,
    "right_shoulder_roll_joint": -0.158,
    "right_shoulder_yaw_joint": -0.546,
    "right_elbow_joint": -0.750,
    # La mano es rígida. Esta orientación la muestra de perfil y evita que
    # parezca una palma abierta saludando.
    "right_wrist_roll_joint": -0.80,
    "right_wrist_pitch_joint": -0.80,
    "right_wrist_yaw_joint": -0.80,
}

_APUNTAR_CIELO = {
    "waist_pitch_joint": -0.08,
    "left_shoulder_pitch_joint": -2.06,
    "left_shoulder_roll_joint": 0.91,
    "left_shoulder_yaw_joint": 0.03,
    "left_elbow_joint": 0.12,
    "left_wrist_pitch_joint": -0.15,
    "right_shoulder_pitch_joint": -2.08,
    "right_shoulder_roll_joint": -1.03,
    "right_shoulder_yaw_joint": 0.05,
    "right_elbow_joint": 0.18,
    "right_wrist_pitch_joint": -0.15,
}

_FINGER_GUNS_PREPARACION = {
    "waist_pitch_joint": -0.06,
    "left_shoulder_pitch_joint": -0.65,
    "left_shoulder_roll_joint": 0.22,
    "left_shoulder_yaw_joint": -0.10,
    "left_elbow_joint": -0.12,
    "left_wrist_pitch_joint": 0.12,
    "left_wrist_yaw_joint": -0.18,
    "right_shoulder_pitch_joint": -0.65,
    "right_shoulder_roll_joint": -0.22,
    "right_shoulder_yaw_joint": 0.10,
    "right_elbow_joint": -0.12,
    "right_wrist_pitch_joint": 0.12,
    "right_wrist_yaw_joint": 0.18,
}
_FINGER_GUNS_DISPARO = {
    "waist_pitch_joint": -0.06,
    "left_shoulder_pitch_joint": -1.50,
    "left_shoulder_roll_joint": 0.30,
    "left_shoulder_yaw_joint": 0.30,
    "left_elbow_joint": 1.30,
    "left_wrist_roll_joint": -0.25,
    "left_wrist_pitch_joint": 0.10,
    "left_wrist_yaw_joint": -0.12,
    "right_shoulder_pitch_joint": -1.50,
    "right_shoulder_roll_joint": -0.30,
    "right_shoulder_yaw_joint": -0.30,
    "right_elbow_joint": 1.30,
    "right_wrist_roll_joint": 0.25,
    "right_wrist_pitch_joint": 0.10,
    "right_wrist_yaw_joint": 0.12,
}
_FINGER_GUNS_RETROCESO = {
    **_FINGER_GUNS_DISPARO,
    "waist_pitch_joint": 0.04,
    "left_shoulder_pitch_joint": -1.34,
    "left_elbow_joint": 1.04,
    "right_shoulder_pitch_joint": -1.34,
    "right_elbow_joint": 1.04,
}


ANIMACIONES: dict[str, Animacion] = {
    "RISA": Animacion(
        3.0,
        (
            _f(0.00),
            _f(0.16, **_RISA_A),
            _f(0.28, **_RISA_B),
            _f(0.40, **_RISA_A),
            _f(0.52, **_RISA_B),
            _f(0.64, **_RISA_A),
            _f(0.76, **_RISA_B),
            _f(1.00),
        ),
    ),
    "BAILE": Animacion(
        4.2,
        (
            _f(0.00),
            _f(0.18, **_BAILE_IZQUIERDA),
            _f(0.31, **_BAILE_DERECHA),
            _f(0.44, **_BAILE_IZQUIERDA),
            _f(0.57, **_BAILE_DERECHA),
            _f(0.70, **_BAILE_IZQUIERDA),
            _f(0.82, **_BAILE_DERECHA),
            _f(1.00),
        ),
    ),
    "BRAZOS_CRUZADOS_COSTADO": Animacion(
        4.6,
        (
            _f(0.00),
            _f(0.11, **_BRAZOS_ABIERTOS_TRANSICION),
            _f(0.22, **_BRAZO_DERECHO_CRUZADO),
            _f(0.31, **_BRAZOS_CRUZADOS),
            _f(0.69, **_BRAZOS_CRUZADOS),
            _f(0.78, **_BRAZO_DERECHO_CRUZADO),
            _f(0.89, **_BRAZOS_ABIERTOS_TRANSICION),
            _f(1.00),
        ),
    ),
    "PULGAR_ARRIBA": Animacion(
        3.1,
        (
            _f(0.00),
            _f(0.25, **_PULGAR_ARRIBA_APROX),
            _f(0.76, **_PULGAR_ARRIBA_APROX),
            _f(1.00),
        ),
    ),
    "APUNTAR_CIELO_DOS_BRAZOS": Animacion(
        3.4,
        (
            _f(0.00),
            _f(0.28, **_APUNTAR_CIELO),
            _f(0.72, **_APUNTAR_CIELO),
            _f(1.00),
        ),
    ),
    "FINGER_GUNS_BANG_BANG": Animacion(
        3.4,
        (
            _f(0.00),
            _f(0.15, **_FINGER_GUNS_PREPARACION),
            _f(0.32, **_FINGER_GUNS_DISPARO),
            _f(0.43, **_FINGER_GUNS_RETROCESO),
            _f(0.53, **_FINGER_GUNS_DISPARO),
            _f(0.64, **_FINGER_GUNS_RETROCESO),
            _f(0.76, **_FINGER_GUNS_DISPARO),
            _f(0.82, **_FINGER_GUNS_DISPARO),
            _f(1.00),
        ),
    ),
}

NOMBRES_EMOTES = tuple(ANIMACIONES)


def obtener_animacion(nombre: str) -> Animacion:
    clave = str(nombre).strip().upper()
    try:
        return ANIMACIONES[clave]
    except KeyError as exc:
        raise ValueError(f"emote simulado desconocido: {nombre}") from exc


def duracion_emote(nombre: str) -> float:
    return obtener_animacion(nombre).duracion


class AnimadorEmotesG1:
    """Convierte un nombre y progreso semanticos en qpos del torso/brazos."""

    def __init__(self, model, mujoco_modulo):
        self.model = model
        self.mj = mujoco_modulo
        self._qpos_por_joint: dict[str, int] = {}
        self._validar_modelo()

    @property
    def direcciones_qpos(self) -> dict[str, int]:
        return dict(self._qpos_por_joint)

    @property
    def tiene_dedos_articulados(self) -> bool:
        marcas = ("finger", "thumb", "index", "middle", "ring", "pinky")
        for joint_id in range(self.model.njnt):
            nombre = self.mj.mj_id2name(
                self.model, self.mj.mjtObj.mjOBJ_JOINT, joint_id
            ) or ""
            if any(marca in nombre.lower() for marca in marcas):
                return True
        return False

    def joints_modificados(self, nombre: str) -> frozenset[str]:
        animacion = obtener_animacion(nombre)
        return frozenset(
            joint
            for fotograma in animacion.fotogramas
            for joint in fotograma.pose
        )

    def aplicar(self, qpos, nombre: str, progreso: float) -> frozenset[str]:
        """Aplica un fotograma interpolado y devuelve los joints escritos."""

        animacion = obtener_animacion(nombre)
        progreso = float(progreso)
        if not math.isfinite(progreso):
            raise ValueError("el progreso del emote debe ser finito")
        progreso = max(0.0, min(1.0, progreso))

        izquierda, derecha = animacion.fotogramas[0], animacion.fotogramas[-1]
        for actual, siguiente in zip(
            animacion.fotogramas, animacion.fotogramas[1:]
        ):
            if actual.progreso <= progreso <= siguiente.progreso:
                izquierda, derecha = actual, siguiente
                break

        intervalo = derecha.progreso - izquierda.progreso
        t = 1.0 if intervalo <= 0.0 else (progreso - izquierda.progreso) / intervalo
        # Smoothstep: velocidad nula en los extremos, sin saltos de qpos.
        t = t * t * (3.0 - 2.0 * t)
        joints = set(izquierda.pose) | set(derecha.pose)
        bases = {joint: float(qpos[self._qpos_por_joint[joint]]) for joint in joints}
        valores = {}
        for joint in joints:
            inicio = float(izquierda.pose.get(joint, bases[joint]))
            fin = float(derecha.pose.get(joint, bases[joint]))
            valores[joint] = inicio + (fin - inicio) * t

        # Primero se calculan y validan todos los valores; recien despues se
        # toca qpos. Asi una excepcion no deja media pose aplicada.
        for joint, valor in valores.items():
            joint_id = self.mj.mj_name2id(
                self.model, self.mj.mjtObj.mjOBJ_JOINT, joint
            )
            minimo, maximo = self.model.jnt_range[joint_id]
            if not (float(minimo) - 1e-9 <= valor <= float(maximo) + 1e-9):
                raise ValueError(f"{joint}={valor} queda fuera de su rango MJCF")
        for joint, valor in valores.items():
            qpos[self._qpos_por_joint[joint]] = valor
        return frozenset(valores)

    def _validar_modelo(self) -> None:
        usados = {
            joint
            for animacion in ANIMACIONES.values()
            for fotograma in animacion.fotogramas
            for joint in fotograma.pose
        }
        desconocidos = usados - JOINTS_SUPERIORES
        if desconocidos:
            raise ValueError(
                "una animacion intenta usar joints no permitidos: "
                + ", ".join(sorted(desconocidos))
            )

        for joint in sorted(usados):
            joint_id = self.mj.mj_name2id(
                self.model, self.mj.mjtObj.mjOBJ_JOINT, joint
            )
            if joint_id < 0:
                raise ValueError(f"el modelo MuJoCo no contiene {joint}")
            if int(self.model.jnt_type[joint_id]) != int(self.mj.mjtJoint.mjJNT_HINGE):
                raise ValueError(f"{joint} no es una articulacion hinge")
            self._qpos_por_joint[joint] = int(self.model.jnt_qposadr[joint_id])

        for nombre, animacion in ANIMACIONES.items():
            anteriores = -1.0
            if animacion.fotogramas[0].progreso != 0.0:
                raise ValueError(f"{nombre} no comienza en neutral")
            if animacion.fotogramas[-1].progreso != 1.0:
                raise ValueError(f"{nombre} no termina en neutral")
            if animacion.fotogramas[0].pose or animacion.fotogramas[-1].pose:
                raise ValueError(f"{nombre} debe comenzar y terminar sin offsets")
            for fotograma in animacion.fotogramas:
                if fotograma.progreso <= anteriores:
                    raise ValueError(f"progreso no creciente en {nombre}")
                anteriores = fotograma.progreso
                for joint, valor in fotograma.pose.items():
                    joint_id = self.mj.mj_name2id(
                        self.model, self.mj.mjtObj.mjOBJ_JOINT, joint
                    )
                    minimo, maximo = self.model.jnt_range[joint_id]
                    if not float(minimo) <= float(valor) <= float(maximo):
                        raise ValueError(
                            f"{nombre}: {joint}={valor} fuera de rango "
                            f"[{minimo}, {maximo}]"
                        )
            for izquierda, derecha in zip(
                animacion.fotogramas, animacion.fotogramas[1:]
            ):
                segundos = (
                    (derecha.progreso - izquierda.progreso) * animacion.duracion
                )
                for joint in set(izquierda.pose) | set(derecha.pose):
                    neutral = POSE_NEUTRAL_G1.get(joint, 0.0)
                    inicio = float(izquierda.pose.get(joint, neutral))
                    fin = float(derecha.pose.get(joint, neutral))
                    # La derivada maxima de smoothstep es 1.5.
                    velocidad = 1.5 * abs(fin - inicio) / segundos
                    if velocidad > VELOCIDAD_VISUAL_MAX_RAD_S + 1e-9:
                        raise ValueError(
                            f"{nombre}: {joint} excede la velocidad visual "
                            f"({velocidad:.2f} rad/s)"
                        )
