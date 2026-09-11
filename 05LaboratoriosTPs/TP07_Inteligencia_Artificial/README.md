# TP07 — Agente de voz y emotes para Unitree G1

Este proyecto permite controlar el G1 incluido en el simulador MuJoCo mediante
órdenes en español escritas o habladas. También incorpora seis emotes animados,
chistes con voz local, modos de movimiento y una evaluación automática.

La configuración está pensada primero para Windows. El reconocimiento y la
síntesis de voz pueden funcionar completamente offline después de instalar las
dependencias y descargar una vez el modelo de voz.

> **Seguridad:** los emotes físicos están habilitados únicamente en el G1 de
> MuJoCo. El backend de emotes para un robot real permanece deshabilitado hasta
> confirmar la variante, las manos, el firmware y el SDK del G1 físico. No se
> deben usar las poses del simulador como órdenes para hardware real.

## 1. Requisitos

- Windows 10 u 11 recomendado. También se incluyen comandos para Linux/macOS.
- Python 3.10 o superior; Python 3.11 es una opción probada.
- Git.
- Una GPU con OpenGL 3.3 para ver la ventana 3D. Una GPU integrada moderna suele
  ser suficiente.
- Micrófono integrado o USB solamente si se desea usar reconocimiento de voz.
- Conexión a Internet para clonar, instalar paquetes y descargar por primera vez
  el modelo STT. Después de eso, el uso normal puede ser offline.

En Windows, conviene instalar Python desde
[python.org](https://www.python.org/downloads/) y marcar `Add python.exe to
PATH` y `py launcher` durante la instalación.

## 2. Clonar el repositorio

Abrir PowerShell o una terminal y ejecutar:

```powershell
git clone https://github.com/tsamaan/UadeRobotLab
cd UadeRobotLab\05LaboratoriosTPs\TP07_Inteligencia_Artificial
```

Todos los comandos de las secciones siguientes suponen que la terminal está en
esa carpeta, es decir, en la raíz de `TP07_Inteligencia_Artificial`.

## 3. Instalación rápida en Windows

Comprobar primero que Python esté disponible:

```powershell
py -3 --version
```

Instalar MuJoCo y la voz local:

```powershell
py -3 -m pip install --upgrade pip
py -3 -m pip install --user mujoco pyttsx3==2.99
```

`mujoco` abre y anima el simulador. `pyttsx3` utiliza las voces instaladas en
Windows y no necesita un servicio cloud. Si la voz local no puede iniciarse, el
programa continúa y muestra el texto en la consola.

Para comprobar la instalación:

```powershell
py -3 -c "import mujoco, pyttsx3; print('Dependencias instaladas')"
```

### Alternativa: entorno virtual

Quien prefiera aislar las dependencias puede usar:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install mujoco pyttsx3==2.99
```

Los lanzadores `.bat` buscan una instalación normal de Python. Para garantizar
que se use el entorno virtual, conviene emplear los comandos directos de la
próxima sección con estos ejecutables:

```powershell
# Simulador: ejecutar desde la raíz del TP
cd entorno
..\.venv\Scripts\python.exe -m sim --robot g1 --materia tp07

# Agente: ejecutar en otra terminal desde la raíz del TP
.\.venv\Scripts\python.exe mi_desarrollo\mi_tp07.py
```

## 4. Ejecutar el simulador y el agente

Se necesitan dos terminales: una mantiene abierto el simulador y la otra ejecuta
el agente.

### Opción sencilla con los lanzadores de Windows

1. Ejecutar `INICIAR_SIMULADOR.bat`, elegir `1 - G1` y esperar a que aparezca la
   ventana 3D.
2. Sin cerrar el simulador, ejecutar `EJECUTAR_MI_CODIGO.bat`.
3. Escribir una orden en el prompt `>` y presionar Enter.

También se pueden abrir los `.bat` con doble clic desde el Explorador.

### Opción directa desde PowerShell

En la primera terminal:

```powershell
cd entorno
py -3 -m sim --robot g1 --materia tp07
```

En una segunda terminal, ubicada otra vez en la raíz del TP:

```powershell
py -3 mi_desarrollo\mi_tp07.py
```

Al iniciar, el agente se conecta, envía una detención preventiva y queda quieto
esperando órdenes. Una línea vacía o `Ctrl+C` cierra el programa.

## 5. Órdenes disponibles

Texto y voz utilizan exactamente el mismo procesamiento. Algunos ejemplos son:

```text
avanzá 2 metros
retrocedé 50 centímetros
girá 90 grados a la derecha
detenete
saludá
estado
modo lento
modo normal
repetí
reversa
ayuda
```

La orden `DETENERSE` tiene prioridad y también cancela de forma segura un emote
que esté en curso.

### Chistes y emotes

```text
contame un chiste
otro chiste
repetí el chiste
contame un chiste y bailá
risa
baile
brazos cruzados
pulgar arriba
apuntá al cielo
finger guns
emote 1
```

Los números de emote son:

| Número | Emote |
|---:|---|
| 1 | Risa |
| 2 | Baile |
| 3 | Brazos cruzados de costado |
| 4 | Pulgar arriba |
| 5 | Apuntar al cielo con ambos brazos |
| 6 | Finger guns, con “bang bang” por TTS |

Las animaciones interpolan las articulaciones del torso y de los brazos, no
alteran la posición global del robot y vuelven a la pose neutral al terminar o
ante un error. El modelo MuJoCo incluido no ofrece manos plenamente articuladas;
por eso `PULGAR_ARRIBA` y `FINGER_GUNS` se representan con poses aproximadas de
brazos y manos.

## 6. Probar visualmente todos los emotes

Primero dejar abierto el simulador con el G1. En otra terminal, desde la raíz del
TP, ejecutar:

```powershell
py -3 mi_desarrollo\probar_emotes.py
```

El menú permite ejecutar cada emote por separado o usar `7 - TODOS`. Esta prueba
no cuenta chistes; `FINGER GUNS` sí reproduce “bang bang”. Para poder evaluar el
resultado visual, no iniciar MuJoCo con `--sin-ventana`.

## 7. Reconocimiento de voz local/offline

Instalar las dependencias opcionales de voz:

```powershell
py -3 -m pip install --user -r requirements-voz.txt
```

Esto instala `faster-whisper`, `sounddevice` y `pyttsx3`. El audio se procesa
localmente; no se envían grabaciones a un servicio cloud.

### Elegir micrófono

Listar los dispositivos disponibles:

```powershell
py -3 mi_desarrollo\mi_tp07.py --list-mics
```

Anotar el índice del micrófono deseado. Si no se pasa `--mic`, se utiliza el
dispositivo predeterminado del sistema.

### Ejecutar el agente por voz

Con el G1 de MuJoCo abierto en otra terminal:

```powershell
py -3 mi_desarrollo\mi_tp07.py --voz --mic 2 --stt-profile quality
```

Reemplazar `2` por el índice obtenido antes. Al comenzar, guardar silencio
durante la calibración de ruido ambiente.

Hay dos perfiles:

- `quality` usa `large-v3`, prioriza la precisión en español y es el
  predeterminado. Requiere más memoria y la primera descarga ocupa varios GB.
- `light` usa `small`, consume menos recursos y carga más rápido, con una posible
  reducción de precisión.

Ejemplo liviano:

```powershell
py -3 mi_desarrollo\mi_tp07.py --voz --stt-profile light
```

La primera ejecución descarga el modelo elegido y necesita Internet. Los modelos
se guardan fuera del repositorio, normalmente en:

```text
%LOCALAPPDATA%\uade-robot-lab\tp07\modelos
```

Una vez descargado el modelo, el reconocimiento funciona sin Internet. Para usar
otra ubicación externa al repositorio:

```powershell
$env:TP07_MODEL_DIR = "D:\modelos\tp07"
py -3 mi_desarrollo\mi_tp07.py --voz --stt-profile quality
```

La ruta configurada no puede estar dentro del repositorio, para evitar versionar
modelos grandes por accidente.

El backend predeterminado trabaja en CPU con cuantización INT8. Una instalación
CUDA compatible puede seleccionarse explícitamente con `--stt-device cuda`; no
es necesaria para el funcionamiento normal.

### Probar voz sin mover el simulador

Esta herramienta escucha, transcribe y muestra qué habría hecho el agente, pero
nunca se conecta ni envía órdenes a un robot:

```powershell
py -3 mi_desarrollo\probar_voz.py --mic 2 --stt-profile quality
```

Es la opción recomendada para calibrar un micrófono nuevo o probar el sistema en
un aula con ruido.

El reconocimiento es deliberadamente conservador: una transcripción vacía,
incierta o ambigua no dispara acciones físicas.

## 8. Modos útiles de ejecución

Ejecutar el modo interactivo sin simulador ni robot:

```powershell
py -3 mi_desarrollo\mi_tp07.py --sin-robot
```

Usar TTS por consola en vez de audio:

```powershell
py -3 mi_desarrollo\mi_tp07.py --tts console
```

Consultar todas las opciones:

```powershell
py -3 mi_desarrollo\mi_tp07.py --help
```

El modo `--sin-robot` sirve para inspeccionar decisiones semánticas. Los emotes
solo se ven físicamente cuando el agente está conectado al simulador G1.

## 9. Evaluación y tests

La evaluación de los 25 casos originales es explícita y no necesita el
simulador:

```powershell
py -3 mi_desarrollo\mi_tp07.py --evaluar
```

El resultado esperado para esta versión es `25/25`, con los tres casos peligrosos
bloqueados.

Para ejecutar la suite completa:

```powershell
cd mi_desarrollo
py -3 -m unittest discover -s tests -v
```

El resultado de referencia actual es `88/88` tests aprobados. Los tests de
MuJoCo requieren que el paquete `mujoco` esté instalado, pero no necesitan abrir
un robot real.

## 10. Linux y macOS

Desde la raíz del TP:

```bash
python3 -m pip install --user mujoco pyttsx3==2.99
chmod +x INICIAR_SIMULADOR.sh EJECUTAR_MI_CODIGO.sh
./INICIAR_SIMULADOR.sh
```

Elegir G1 y, en otra terminal:

```bash
./EJECUTAR_MI_CODIGO.sh
```

Para voz:

```bash
python3 -m pip install --user -r requirements-voz.txt
python3 mi_desarrollo/mi_tp07.py --list-mics
python3 mi_desarrollo/mi_tp07.py --voz --mic 0 --stt-profile quality
```

Según el sistema, `sounddevice` puede requerir que PortAudio esté instalado con
el gestor de paquetes de la distribución. El desarrollo y las primeras pruebas
de este TP se realizaron en Windows.

## 11. Solución de problemas

### `py` o `python` no se reconoce

Reinstalar Python desde python.org, habilitar el lanzador `py` y abrir una
terminal nueva. En Windows, el alias de Microsoft Store puede abrir la tienda en
vez de ejecutar Python; usar `py -3` evita normalmente ese problema.

### MuJoCo informa que falta una DLL

Instalar el
[Microsoft Visual C++ Redistributable x64](https://aka.ms/vs/17/release/vc_redist.x64.exe),
reiniciar la terminal y volver a ejecutar el simulador.

### El simulador abre sin ventana o falla OpenGL

Actualizar el controlador de video y ejecutar desde una sesión de escritorio
local. Las máquinas virtuales y algunas sesiones remotas pueden no ofrecer
OpenGL 3.3. Para diagnóstico sin interfaz puede usarse:

```powershell
cd entorno
py -3 -m sim --robot g1 --materia tp07 --sin-ventana
```

Ese modo no sirve para verificar visualmente los emotes.

### El agente no se conecta

- Confirmar que el simulador esté abierto antes que el agente.
- Elegir G1 y el perfil `tp07`.
- Verificar que no haya dos simuladores intentando usar el puerto local `8765`.
- Cerrar procesos viejos con `Ctrl+C` y volver a iniciar ambas terminales.

La ejecución local normal usa un socket y no necesita CycloneDDS ni el SDK de
Unitree.

### No aparece el micrófono

- Dar permiso de micrófono a las aplicaciones de escritorio en la configuración
  de privacidad de Windows.
- Reconectar el micrófono USB y repetir `--list-mics`.
- Probar otro índice con `--mic`.
- Cerrar otras aplicaciones que estén usando el dispositivo en modo exclusivo.

### El reconocimiento tarda demasiado o se queda sin memoria

Usar el perfil liviano:

```powershell
py -3 mi_desarrollo\mi_tp07.py --voz --stt-profile light
```

### No se escucha el TTS

Comprobar el volumen y que Windows tenga una voz instalada. Reinstalar
`pyttsx3` o usar `--tts console`; las acciones y los logs siguen funcionando
aunque no haya salida de audio.

### La descarga del modelo se interrumpió

Comprobar la conexión y repetir el mismo comando. `faster-whisper` reutiliza lo
que ya esté correctamente almacenado en la caché. No copiar el modelo dentro del
repositorio.

## 12. Estructura relevante

```text
TP07_Inteligencia_Artificial/
├── entorno/sim/                 # MuJoCo, modelo G1 y servidor local
├── mi_desarrollo/
│   ├── mi_tp07.py               # agente principal
│   ├── voz.py                   # captura y STT local
│   ├── tts.py                   # TTS local con fallback
│   ├── emotes.py                # nombres semánticos y selección
│   ├── simulador_emotes.py      # puente hacia el simulador
│   ├── probar_emotes.py         # menú visual de emotes
│   ├── probar_voz.py            # prueba segura sin robot
│   └── tests/                   # suite automática
├── requirements-voz.txt
├── INICIAR_SIMULADOR.bat/.sh
└── EJECUTAR_MI_CODIGO.bat/.sh
```

Los modelos MuJoCo necesarios ya están incluidos en el repositorio. No hay que
descargar un XML/MJCF adicional ni configurar manualmente nombres o índices de
articulaciones.

## 13. Alcance del robot real

La detección de capacidades distingue entre simulador y hardware. Mientras no se
confirmen la variante exacta del G1, sus manos, firmware y SDK:

- se pueden probar todos los emotes en MuJoCo;
- los logs y nombres semánticos permanecen disponibles;
- no se habilitan poses ni emotes físicos sobre un G1 real;
- no se inventan llamadas de SDK, índices ni posiciones articulares.

Para más detalles técnicos consultar
[`README_VOZ_EMOTES.md`](README_VOZ_EMOTES.md),
[`mi_desarrollo/EMOTES_SIMULADOR.md`](mi_desarrollo/EMOTES_SIMULADOR.md) e
[`INSTALACION.md`](INSTALACION.md).
