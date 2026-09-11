"""Menu manual para ver los seis emotes en el G1 de MuJoCo."""

from __future__ import annotations

import time

from capacidades_robot import detectar_capacidades
from emotes import crear_emote_manager
from robot import Robot
from tts import crear_tts


OPCIONES = {
    "1": ("RISA", "RISA"),
    "2": ("BAILE", "BAILE"),
    "3": ("BRAZOS CRUZADOS", "BRAZOS_CRUZADOS_COSTADO"),
    "4": ("PULGAR ARRIBA", "PULGAR_ARRIBA"),
    "5": ("APUNTAR AL CIELO", "APUNTAR_CIELO_DOS_BRAZOS"),
    "6": ("FINGER GUNS", "FINGER_GUNS_BANG_BANG"),
}


def _mostrar_menu() -> None:
    print("\nEMOTES DEL G1 EN MUJOCO")
    for numero, (etiqueta, _nombre) in OPCIONES.items():
        print(f"{numero} - {etiqueta}")
    print("7 - TODOS")
    print("0 - SALIR")


def _esperar_fin(robot: Robot, timeout: float = 10.0) -> None:
    limite = time.monotonic() + timeout
    while time.monotonic() < limite:
        estado = robot.verificar_estado()
        if estado.emote is None:
            return
        time.sleep(0.05)
    robot.cancelar_emote_simulado()
    raise TimeoutError("el emote no termino dentro del tiempo esperado")


def _probar(manager, robot: Robot, nombre: str) -> None:
    print(f"\nProbando {nombre}...")
    if not manager.ejecutar(nombre):
        raise RuntimeError(f"el simulador rechazo {nombre}")
    _esperar_fin(robot)
    print(f"[OK] {nombre} termino y volvio a neutral.")


def main() -> int:
    robot = Robot()
    robot.conectar()
    if robot.modelo != "g1" or robot.destino != "simulador":
        robot.desconectar()
        print("Este script requiere el G1 abierto en el simulador local.")
        return 1

    capacidades = detectar_capacidades(robot)
    # Offline: usa la voz instalada en Windows y cae a consola si no puede
    # inicializarla. FINGER_GUNS inicia la pose antes de decir "bang bang".
    tts = crear_tts(capacidades, usar_local=True)
    manager = crear_emote_manager(
        capacidades, robot=robot, hablar=tts.hablar
    )

    try:
        while True:
            _mostrar_menu()
            opcion = input("\nElegir: ").strip()
            if opcion in ("", "0"):
                break
            if opcion == "7":
                for _etiqueta, nombre in OPCIONES.values():
                    _probar(manager, robot, nombre)
                    time.sleep(0.25)
                continue
            seleccionado = OPCIONES.get(opcion)
            if seleccionado is None:
                print("Opcion invalida.")
                continue
            _probar(manager, robot, seleccionado[1])
    except KeyboardInterrupt:
        print("\nPrueba cancelada.")
    finally:
        # StopMove cancela cualquier emote pendiente y el visor recompone la
        # pose neutral en su siguiente frame.
        try:
            tts.detener()
            robot.cancelar_emote_simulado()
        finally:
            robot.desconectar()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
