"""Ventana 3D con el modelo OFICIAL del robot.

No corre fisica: escribe la pose y llama mj_forward. Ver robots.py para el
porque.
"""

from __future__ import annotations

import math
import time

from .robots import Robot as RobotSim


def mujoco_disponible() -> tuple[bool, str]:
    try:
        import mujoco  # noqa: F401
        import mujoco.viewer  # noqa: F401
        return True, ""
    except Exception as exc:
        return False, str(exc)


class Visor:
    def __init__(self, mundo, robot: RobotSim):
        import mujoco

        ruta = robot.ruta_escena()
        if ruta is None:
            from .robots import faltan_modelos
            raise FileNotFoundError(faltan_modelos())

        self.mundo = mundo
        self.robot = robot
        self.mj = mujoco
        self.model = mujoco.MjModel.from_xml_path(ruta)
        self.data = mujoco.MjData(self.model)
        self.ruta = ruta
        # Sin gravedad: el modelo no tiene que caerse mientras lo posicionamos.
        self.model.opt.gravity[:] = 0.0
        self._primera_art = 7   # qpos[0:3] posicion, qpos[3:7] cuaternion
        self.animador_emotes = None
        if self.robot.clave == "g1":
            from .emotes_g1 import AnimadorEmotesG1

            self.animador_emotes = AnimadorEmotesG1(self.model, self.mj)

    def _pose(self) -> None:
        e = self.mundo.leer()
        q = self.data.qpos

        q[0] = e["x"]
        q[1] = e["y"]
        q[2] = self.robot.altura
        media = e["yaw"] / 2.0
        q[3], q[4], q[5], q[6] = math.cos(media), 0.0, 0.0, math.sin(media)

        art = q[self._primera_art:]
        art[:] = 0.0
        for idx, valor in self.robot.pose_de_pie.items():
            if idx < len(art):
                art[idx] = valor

        if e.get("emote") is not None:
            self._aplicar_emote_seguro(e)
        elif e["accion"] in ("saludo", "saludando", "dar_la_mano", "besando"):
            for idx, valor in self.robot.saludo.items():
                if idx < len(art):
                    art[idx] = valor + (
                        0.35 * math.sin(time.time() * 7.0)
                        if e["accion"] in ("saludo", "saludando") else 0.0
                    )
        elif e["moviendose"]:
            f = e["fase"]
            for idx, amplitud, desfase in self.robot.marcha:
                if idx < len(art):
                    art[idx] += amplitud * math.sin(f + desfase)

        self.mj.mj_forward(self.model, self.data)

    def _aplicar_emote_seguro(self, estado) -> None:
        if self.animador_emotes is None:
            self.mundo.cancelar_emote()
            return
        q = self.data.qpos
        direcciones = self.animador_emotes.direcciones_qpos
        neutral = {direccion: float(q[direccion]) for direccion in direcciones.values()}
        aplicado = False
        try:
            self.animador_emotes.aplicar(
                q,
                estado["emote"],
                float(estado.get("progreso_emote", 0.0)),
            )
            aplicado = True
        except Exception as exc:                              # noqa: BLE001
            self.mundo.avisos.append(
                f"emote cancelado y neutralizado: {type(exc).__name__}: {exc}"
            )
        finally:
            if not aplicado:
                for direccion, valor in neutral.items():
                    q[direccion] = valor
                self.mundo.cancelar_emote()

    def correr(self, hz: float = 50.0) -> None:
        import mujoco.viewer

        periodo = 1.0 / hz
        with mujoco.viewer.launch_passive(
            self.model, self.data, show_left_ui=False, show_right_ui=False
        ) as v:
            v.cam.distance = 3.5 if self.robot.tipo == "humanoide" else 2.6
            v.cam.elevation = -20
            while v.is_running():
                inicio = time.perf_counter()
                self.mundo.avanzar()
                self._pose()
                v.sync()
                resto = periodo - (time.perf_counter() - inicio)
                if resto > 0:
                    time.sleep(resto)


def correr_sin_ventana(mundo, hz: float = 50.0, detener=None) -> None:
    periodo = 1.0 / hz
    while detener is None or not detener.is_set():
        mundo.avanzar()
        time.sleep(periodo)
