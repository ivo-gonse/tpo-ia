# Extension de voz y emotes — TP07

La extension conserva un unico pipeline de decisiones:

`audio -> STT -> texto -> AgenteRobot.procesar(texto) -> validar -> ejecutar`

El modo texto no requiere dependencias adicionales. Para preparar el modo voz en
Windows:

```powershell
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-voz.txt
```

Los modelos no se guardan dentro del repositorio. `TP07_MODEL_DIR` permite elegir
un directorio local; si no se define se usa la cache de usuario de la plataforma.
La primera descarga requiere Internet, pero la ejecucion configurada usa archivos
locales y no depende de servicios cloud.

La configuracion inicial supone `faster-whisper` sobre CPU con cuantizacion INT8.
El microfono se seleccionara de una lista de dispositivos y se calibrara con ruido
ambiente. Una transcripcion dudosa se bloquea antes de cualquier accion fisica.

Perfiles disponibles:

- `quality` (predeterminado): Whisper `large-v3`, maxima precision; reservar
  aproximadamente 3 GB para el modelo y se recomienda una PC con 16 GB de RAM.
- `light`: Whisper `small`, aproximadamente 1 GB descargado y menor uso de CPU/RAM.

Ambos funcionan en CPU INT8; `--stt-device cuda` es opcional y requiere una
instalacion CUDA/cuDNN compatible con CTranslate2. La primera carga descarga el
modelo a `TP07_MODEL_DIR` (o a la cache externa predeterminada); las siguientes
cargas lo reutilizan y pueden ejecutarse offline. Para provisionar una notebook,
se instalan primero las dependencias y el modelo mientras haya Internet.

Licencias de las dependencias fijadas: faster-whisper y CTranslate2 (MIT),
sounddevice (MIT), modelo `openai/whisper-large-v3` (Apache-2.0 segun su model
card) y pyttsx3 (MPL-2.0). Revisar de nuevo las licencias antes de redistribuir
modelos o empaquetar binarios.

Uso:

```powershell
# Programa final por texto: conecta al simulador y queda esperando
py -3 mi_desarrollo/mi_tp07.py

# Evaluacion original, sólo cuando se solicita
py -3 mi_desarrollo/mi_tp07.py --evaluar

# Enumerar y seleccionar microfono
py -3 mi_desarrollo/mi_tp07.py --list-mics
py -3 mi_desarrollo/mi_tp07.py --voz --mic 2 --stt-profile quality

# Interactivo sin conectar un robot
py -3 mi_desarrollo/mi_tp07.py --sin-robot

# Herramienta manual: siempre sin robot
py -3 mi_desarrollo/probar_voz.py --mic 2 --stt-profile light
```

Los umbrales (`idioma >= 0.70`, `avg_logprob >= -0.75` y
`no_speech_prob <= 0.35`) son heuristicas deliberadamente conservadoras: Whisper
no entrega una confianza calibrada comparable entre audios. Ademas se exige una
frase corta con una intencion reconocible; no se corrigen por aproximacion palabras
de movimiento. Los valores se deben ajustar con `frases_validacion_voz.txt` y
grabaciones representativas del aula, sin habilitar robot real durante el ajuste.

Los emotes se prueban primero en simulacion. Para robot real comienzan todos
deshabilitados hasta confirmar variante G1, manos, firmware, SDK y lista de acciones
expuesta en tiempo de ejecucion. No se definen posiciones articulares supuestas.

## Chistes y TTS

`chistes.py` contiene exactamente 100 chistes y una bolsa aleatoria que no repite
hasta agotar una ronda. `otro chiste` elige uno nuevo; `repeti` despues de un
chiste dice exactamente el mismo, porque repite la accion semantica almacenada.

La salida predeterminada (`--tts local`) intenta usar una voz instalada mediante
pyttsx3 y vuelve a `[ROBOT] <texto>` en consola ante cualquier error. Para una
prueba silenciosa se puede indicar `--tts console`.
El adaptador Unitree solo acepta un `AudioClient` inyectado, el metodo oficial
`TtsMaker`, un `speaker_id` configurado y las capacidades del hardware confirmadas;
con el G1 actual todavia desconocido no se selecciona automaticamente.

## Emotes y capacidades

Los seis emotes existen como nombres semanticos y se eligen sin repeticion
consecutiva. En simulacion generan `[EMOTE] NOMBRE` y una animacion visible real
de torso, brazos y muñecas. Se pueden pedir por `emote 1..6` o por expresiones
como `baile`, `brazos cruzados`, `pulgar arriba`, `apuntá al cielo` y `pistolas`.
Un chiste sin gesto concreto elige exactamente un emote aleatorio; si la frase
menciona uno, ejecuta solamente ese. En hardware real, cinco permanecen sin
implementacion fisica y `APUNTAR_CIELO_DOS_BRAZOS` solo puede mapearse a la accion
oficial `hands up` si aparece al consultar el cliente en runtime. Tambien se exige
`release arm` para volver a neutral.

La ruta real requiere inventario confirmado de variante, manos, firmware y SDK,
estado/bateria valida, locomocion detenida y un cliente oficial inyectado. Ante una
excepcion intenta neutral, registra el error y el agente sigue operativo. No hay
posiciones articulares ni identificadores numericos en este TP. La cancelacion se
atiende en limites entre comandos; no se agregaron threads porque no esta confirmada
la seguridad concurrente del SDK del robot concreto.

Pruebas automáticas (nunca se disparan desde el arranque interactivo):

```powershell
cd mi_desarrollo
py -3 -m unittest discover -s tests -v
```
