"""Prueba manual de STT que nunca conecta ni envia ordenes a un robot."""

import argparse

from mi_tp07 import AgenteRobot
from voz import CapturadorMicrofono, ErrorVoz, ReconocedorVozLocal, procesar_una_orden_por_voz


def main():
    parser = argparse.ArgumentParser(description="Prueba segura de voz del TP07")
    parser.add_argument("--list-mics", action="store_true")
    parser.add_argument("--mic", type=int, default=None)
    parser.add_argument("--stt-profile", choices=("quality", "light"), default="quality")
    parser.add_argument("--stt-device", choices=("cpu", "cuda"), default="cpu")
    args = parser.parse_args()

    if args.list_mics:
        try:
            dispositivos = CapturadorMicrofono().listar_microfonos()
        except ErrorVoz as exc:
            print(f"No se pudieron listar microfonos: {exc}")
            return
        for d in dispositivos:
            print(f"{d.indice}: {d.nombre} ({d.frecuencia_predeterminada:g} Hz)")
        return

    reconocedor = ReconocedorVozLocal(args.stt_profile, args.stt_device)
    agente = AgenteRobot(robot=None)
    print("PRUEBA SIN ROBOT: guarda silencio un segundo para calibrar.")
    try:
        print(f"Umbral RMS: {reconocedor.calibrar(args.mic):.4f}")
        while True:
            input("\nEnter para escuchar; Ctrl+C para salir... ")
            resultado = procesar_una_orden_por_voz(agente, reconocedor, args.mic)
            estado = "BLOQUEAR" if resultado["bloqueado"] else (
                "EJECUTAR" if resultado["ejecutar"] else "DESCONOCIDO"
            )
            print(f"Original: {resultado['transcripcion_original']}")
            print(f"Tipo: {resultado['tipo']}")
            print(f"Parametros: {resultado['parametros']}")
            print(f"Decision: {estado} — {resultado['mensaje']}")
    except KeyboardInterrupt:
        print("\nFin de la prueba.")
    except ErrorVoz as exc:
        print(f"Error de voz: {exc}")


if __name__ == "__main__":
    main()
