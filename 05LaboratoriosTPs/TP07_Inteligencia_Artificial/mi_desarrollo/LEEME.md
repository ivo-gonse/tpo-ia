# Tu carpeta de trabajo — TP07

| Archivo | Para qué |
|---|---|
| `mi_tp07.py` | Acá escribís tu agente. **Es lo que entregás.** |
| `casos_prueba.json` | Los 25 casos de la cátedra. Dados hechos. |
| `evaluar.py` | Dado hecho. Calcula tu accuracy y la tabla de fallos. |
| `ejecutor.py` | Dado hecho. Convierte a velocidad y tiempo, y manda al robot. |
| `robot.py` | No lo toques. |
| `dataset.csv` | **Extensión**: 5 ejemplos para que veas el formato. Completalo vos. |
| `entrenar.py` | Dado hecho. Entrena con tu dataset y te da las métricas. |

## Cómo lo ejecutás

**Con robot** (para ver al G1 hacerte caso):

1. Abrí `INICIAR_SIMULADOR` y elegí el robot.
2. Doble clic en `EJECUTAR_MI_CODIGO`, o `python3 mi_desarrollo/mi_tp07.py`.

**Sin robot** (mismo modo interactivo, sin conexión física):

```
python3 mi_desarrollo/mi_tp07.py --sin-robot
```

La evaluación no se ejecuta al arrancar. Para correr explícitamente los 25
casos, usá:

```
python3 mi_desarrollo/mi_tp07.py --evaluar
```

## Probar los emotes físicos en MuJoCo

1. Abrí `INICIAR_SIMULADOR`, elegí `G1` y dejá visible la ventana 3D.
2. En otra terminal entrá en `mi_desarrollo`.
3. Ejecutá:

```powershell
py -3 probar_emotes.py
```

El menú permite probar cada emote por separado o los seis en secuencia, sin
contar chistes. `FINGER GUNS` también dice “bang bang” con TTS local y cae a
salida de consola si Windows no ofrece una voz compatible.

## Programa interactivo único

Con el robot conectado queda quieto y espera órdenes desde el primer prompt:

```
  > avanzá 2 metros
  > girá 90 grados a la derecha
  > baile
  > emote 4
  > contame un chiste y bailá
  > ayuda
```

`--voz` cambia sólo la entrada: texto y voz pasan por el mismo
`AgenteRobot.procesar(texto)`.

## Extensión: entrenar un modelo (nivel 2)

Con reglas alcanza para aprobar. Si querés ir más lejos:

**1. Armá tu dataset.** `dataset.csv` trae 5 ejemplos para que veas el formato:

```
texto,intencion
dale para adelante,MOVER
frená ahí,DETENERSE
```

Completalo hasta unos 80. Las intenciones válidas son `MOVER`, `GIRAR`,
`DETENERSE`, `SALUDO`, `CONSULTAR_ESTADO` y `DESCONOCIDO`.

**2. Entrená y mirá tus métricas:**

```
python3 mi_desarrollo/entrenar.py
```

Te avisa si al dataset le falta algo: pocas filas, una intención sin ejemplos,
textos repetidos.

**3. Usalo en tu agente.** En `ClasificadorIntencion.__init__` hay dos líneas
comentadas:

```python
from entrenar import entrenar_desde_csv
self.modelo = entrenar_desde_csv()
```

Y en `clasificar()`:

```python
if self.modelo is not None:
    return self.modelo.predict([texto])[0]
```

Dejá las reglas de respaldo: si el dataset no está, el agente sigue andando.

**El extractor, el validador y el ejecutor no se enteran.** Cambiás una sola
clase.

**4. Compará.** ¿El modelo le gana a tus reglas? ¿En qué casos pierde? Esa
comparación es parte del informe.

> Necesitás `scikit-learn`: `pip install --user scikit-learn`.
> Sin él, el TP se hace igual con reglas.

## Qué entregás si hiciste la extensión

Una **carpeta** con los dos archivos:

```
tp07_apellido/
├── mi_tp07.py
└── dataset.csv
```

No hace falta que entregues el modelo entrenado: se entrena solo al arrancar,
en milisegundos. Y así el profesor puede **leer** tu dataset.
