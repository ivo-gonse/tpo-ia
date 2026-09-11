# Reporte de extensiones — TP07 Inteligencia Artificial

Fecha de verificacion: 10 de septiembre de 2026. Rama local:
`feature/tp07-voz-emotes`.

## Resultado

El agente extendido conserva un solo pipeline:

`texto/voz -> intencion -> parametros/estado -> validacion -> adapter/ejecutor -> robot`

La voz nunca invoca al robot: una transcripcion confirmada llama a
`AgenteRobot.procesar(texto_normalizado)` y una dudosa llama al mismo metodo con
la marca `[VOZ NO CONFIRMADA]`, que el validador bloquea. Repetir y reversa
reconstruyen copias semanticas, vuelven a validar y aplican el modo actual antes
de llegar al ejecutor.

Resultados ejecutados:

- Casos originales: **25/25 (100 %)**, con **3/3** peligrosos bloqueados.
- Tests nuevos: **70/70**, incluidas las 25 intenciones, microfono/modelo ausente,
  numeros hablados, fallos de transporte y casos adversariales.
- Compilacion: `python -m compileall -q .`, sin errores.
- Smoke CLI: `--help`, `--sin-robot` y `--list-mics`, correctos.
- Simulador: revision de MuJoCo/modelos correcta y smoke headless real contra el
  socket local correcto (modo lento, avance 0.1 m, reversa, chiste+emote y stop).
- Voz manual sin robot: microfono 18, calibracion RMS 0.0080; silencio durante
  cinco segundos produjo timeout controlado y ninguna accion.

No se ejecuto voz hablada ni se descargo un modelo Whisper durante la prueba
manual. Por lo tanto, no hay un WER, accuracy de intencion acustica ni tasa real
de falsos positivos que se pueda afirmar todavia. La integracion STT se verifico
con backend mock y metricas simuladas.

## Arquitectura final

- `mi_tp07.py`: clasificador, extractor, validador y orquestacion unica.
- `estado_agente.py`: modo lento, historial, ultima accion y ultimo movimiento.
- `voz.py`: dispositivos, captura/VAD por energia, faster-whisper, confianza y
  puente al agente.
- `configuracion.py`: perfiles y rutas de modelos externas al repositorio.
- `chistes.py`: banco cerrado de 100 y bolsa aleatoria sin repeticion.
- `tts.py`: consola, pyttsx3 local y cliente Unitree confirmado con fallback.
- `capacidades_robot.py`: deteccion conservadora de simulador/inventario/runtime.
- `emotes.py`: catalogo semantico, seleccion y backends simulado/real confirmado.
- `probar_voz.py`: prueba manual que construye el agente sin robot.
- `tests/`: unitarios, integracion con mocks y casos adversariales.

El estado del agente incluye `modo_lento`, historial, ultima accion ejecutada,
ultimo movimiento reversible y estado de TTS/emote. `REPETIR` no se guarda como
accion: reproduce la accion semantica previa. Despues de un chiste repite el mismo
texto; `otro chiste` consume uno nuevo. `REVERSA` solo invierte avance/retroceso o
izquierda/derecha y se describe siempre como compensacion aproximada.

## Dependencias y ejecucion offline

Instalacion ejecutada en Windows con Python 3.11.4:

```powershell
py -3 -m pip install --user -r requirements-voz.txt mujoco
```

Versiones verificadas: faster-whisper 1.2.1, CTranslate2 4.8.2, sounddevice
0.5.6, pyttsx3 2.99 y MuJoCo 3.13.0. El perfil `quality` usa Whisper large-v3
en CPU INT8; `light`, Whisper small. La primera carga necesita descargar el
modelo a la cache externa (`TP07_MODEL_DIR` permite cambiarla); una vez presente,
STT y TTS local no requieren Internet. El modo texto no importa estas dependencias.

La captura enumera dispositivos, permite `--mic`, intenta 16 kHz mono, usa la
frecuencia nativa si hace falta y remuestrea. Calibra ruido ambiente, conserva
prebuffer, corta por silencio/timeout, limita la frase a ocho segundos y descarta
la orden completa ante overflow.

### Decision tecnica y fuentes oficiales

| Opcion STT local | Espanol/calidad | Windows/CPU | Streaming | Decision |
|---|---|---|---|---|
| faster-whisper/CTranslate2 | modelos Whisper multilingues, large-v3 | wheels Windows, INT8 CPU | VAD y transcripcion por segmentos | principal |
| whisper.cpp | mismos modelos cuantizables | compatible, binario/compilacion adicional | ejemplos streaming/VAD | fallback de despliegue, no integrado |
| Vosk | modelo espanol chico y grande | muy liviano | streaming nativo/vocabulario | fallback de hardware limitado, no integrado |
| sherpa-onnx | toolkit amplio; sin ventaja espanola medida aqui | multiplataforma | streaming/no streaming | candidato futuro |

Se eligio faster-whisper porque prioriza precision en espanol, tiene instalacion
directa en Windows, CPU INT8, VAD integrado y carga desde cache local. `large-v3`
es el perfil de maxima calidad; `small`, el perfil liviano. Vosk no se incorpora
al runtime actual para evitar dos pipelines sin una evaluacion acustica que
justifique la complejidad.

Fuentes consultadas:

- [faster-whisper (PyPI)](https://pypi.org/project/faster-whisper/)
- [CTranslate2 (PyPI)](https://pypi.org/project/ctranslate2/)
- [OpenAI Whisper](https://github.com/openai/whisper/blob/main/README.md) y
  [model card large-v3](https://huggingface.co/openai/whisper-large-v3)
- [whisper.cpp](https://github.com/ggml-org/whisper.cpp/blob/master/README.md)
- [Vosk y modelos](https://alphacephei.com/vosk/models)
- [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx/blob/master/README.md)
- [sounddevice (PyPI)](https://pypi.org/project/sounddevice/) y
  [pyttsx3 (PyPI)](https://pypi.org/project/pyttsx3/)
- [AudioClient oficial G1](https://github.com/unitreerobotics/unitree_sdk2_python/blob/master/unitree_sdk2py/g1/audio/g1_audio_client.py)
- [Ejemplo oficial de audio G1](https://github.com/unitreerobotics/unitree_sdk2_python/blob/master/example/g1/audio/g1_audio_client_example.py)
- [Cliente oficial de acciones de brazo](https://github.com/unitreerobotics/unitree_sdk2/blob/main/include/unitree/robot/g1/arm/g1_arm_action_client.hpp)
- [Ejemplo oficial Python de acciones G1](https://github.com/unitreerobotics/unitree_sdk2_python/blob/master/example/g1/high_level/g1_arm_action_example.py)
- [Ejemplo oficial Dex3](https://github.com/unitreerobotics/unitree_sdk2/blob/main/example/g1/dex3/g1_dex3_example.cpp)
- [Servicio oficial Linker Hand O6](https://github.com/unitreerobotics/linker_hand_service)

## Emotes realmente disponibles

En simulacion estan disponibles los seis como eventos `[EMOTE]`:

| Emote | Implementacion declarada | Robot real actual |
|---|---|---|
| RISA | simulated_only | deshabilitado |
| BAILE | simulated_only | deshabilitado |
| BRAZOS_CRUZADOS_COSTADO | custom_pose | deshabilitado |
| PULGAR_ARRIBA | custom_pose, requiere manos | deshabilitado |
| APUNTAR_CIELO_DOS_BRAZOS | native candidata `hands up` | deshabilitado |
| FINGER_GUNS_BANG_BANG | custom_pose, requiere manos | deshabilitado |

Para una configuracion futura confirmada, solo la candidata nativa se habilita
si `GetActionList` informa en runtime `hands up` y `release arm`. El backend frena
locomocion, exige telemetria de bateria confirmada, verifica estado, ejecuta la accion por nombre y vuelve a
neutral en `finally`. No hay angulos, limites articulares ni IDs supuestos.

## Seguridad y riesgos conocidos

- El validador corre incluso para intenciones desconocidas, metaordenes, replay y
  reversa. Rechaza palabras peligrosas, distancia mayor a 5 m, angulo mayor a
  180 grados, velocidad superior al perfil, valores invalidos y bateria baja o
  desconocida antes de locomocion/saludo.
- El modo lento opera sobre copias y conserva distancia mediante mas tiempo y
  tramos ya limitados por el ejecutor.
- STT, chistes y emotes no tienen referencias de locomocion. El backend real de
  emotes solo puede frenar y llamar acciones oficiales verificadas.
- Los fallos de STT, TTS o emote se contienen y no derriban el agente.
- `DETENERSE` gana prioridad en clasificacion (`no avances` incluido), llama al
  ejecutor y cancela TTS/emote activo en un limite entre comandos.
- Limitacion: la CLI es secuencial y no puede recibir una nueva orden mientras
  una llamada nativa de TTS/SDK ya esta bloqueada. No se agregaron threads porque
  no esta confirmada la seguridad concurrente ni la semantica de cancelacion del
  SDK/firmware exacto. El cambio minimo futuro es un unico worker de presentacion
  con cancel token y un canal de stop oficialmente thread-safe; debe validarse en
  banco antes de habilitarlo.
- El wrapper compartido puede usar 87 % como bateria de respaldo si no hay dato.
  Por eso, cualquier locomocion o emote real queda bloqueado hasta declarar y
  probar `telemetria_bateria_confirmada`; el valor de respaldo no habilita nada.
- Los numeros espanoles de cero a mil usados con metros, grados o metros por
  segundo se interpretan antes de validar. Una unidad con magnitud ininteligible
  se bloquea en lugar de caer a un valor predeterminado.
- El filtro de confianza usa heuristicas, no probabilidades calibradas. Los
  umbrales deben medirse con voces reales y ruido del aula; los falsos negativos
  son preferibles a falsos comandos fisicos.

## Pendiente antes de un robot real

1. Registrar variante exacta del G1, manos, firmware y version/commit del SDK.
2. Confirmar en el robot los servicios de audio, idioma/espanol y `speaker_id`.
3. Consultar acciones de brazo en runtime y conservar una allowlist aprobada.
4. Verificar retorno a neutral, bateria, stop y timeouts en un banco despejado,
   con operador y parada fisica disponible.
5. Grabar un corpus consentido de las frases de validacion en el aula; medir WER,
   accuracy de intencion y, especialmente, falsos positivos inseguros.
6. Ajustar umbrales sin conectar locomocion; recien despues repetir en simulacion.
7. Mantener deshabilitadas todas las poses custom hasta contar con limites y
   validacion de colision oficiales para esa configuracion exacta.
