"""Adaptador semantico entre el agente y el simulador local."""

from __future__ import annotations


class SimuladorEmotes:
    """Envia nombres de emote; no conoce MuJoCo, joints, indices ni qpos."""

    def __init__(self, robot):
        self.robot = robot
        if getattr(robot, "destino", None) != "simulador":
            raise ValueError("SimuladorEmotes no puede conectarse a un robot real")
        if getattr(robot, "transporte", None) != "local":
            raise ValueError("los emotes visuales requieren el transporte local")
        if getattr(robot, "modelo", None) != "g1":
            raise ValueError("los emotes visuales requieren el modelo G1")

    def ejecutar_emote(self, nombre: str) -> None:
        ejecutar = getattr(self.robot, "ejecutar_emote_simulado", None)
        if not callable(ejecutar):
            raise RuntimeError("la API del simulador no expone emotes visuales")
        ejecutar(str(nombre).strip().upper())

    def cancelar(self) -> None:
        cancelar = getattr(self.robot, "cancelar_emote_simulado", None)
        if callable(cancelar):
            cancelar()
        else:
            # StopMove tambien cancela en Mundo y permite degradar con una
            # version anterior del cliente local.
            self.robot.detenerse()
