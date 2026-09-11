# Emotes físicos en el simulador G1

## Modelo inspeccionado

El arranque efectivo es `sim.__main__ -> SimuladorLocal -> SimuladorOficial`.
La escena cargada es `entorno/sim/unitree_mujoco/unitree_robots/g1/scene_29dof.xml`,
que incluye `g1_29dof.xml`. El modelo compilado por MuJoCo 3.13.0 informa:

- `nq = 36`, `nv = 35`, `nu = 29`, `njnt = 30`;
- `qpos[0:7]`: `floating_base_joint` (posición y cuaternión);
- `qpos[7:19]`: piernas;
- `qpos[19:22]`: cintura/torso;
- `qpos[22:29]`: brazo y muñeca izquierdos;
- `qpos[29:36]`: brazo y muñeca derechos.

Inventario obtenido del `MjModel` compilado (no supuesto):

| Joint real | qpos | Actuador | Índice actuador | Rango MJCF (rad) |
|---|---:|---|---:|---:|
| `floating_base_joint` | 0..6 | — | — | libre |
| `left_hip_pitch_joint` | 7 | `left_hip_pitch` | 0 | -2.53070 .. 2.87980 |
| `left_hip_roll_joint` | 8 | `left_hip_roll` | 1 | -0.52360 .. 2.96710 |
| `left_hip_yaw_joint` | 9 | `left_hip_yaw` | 2 | -2.75760 .. 2.75760 |
| `left_knee_joint` | 10 | `left_knee` | 3 | -0.08727 .. 2.87980 |
| `left_ankle_pitch_joint` | 11 | `left_ankle_pitch` | 4 | -0.87267 .. 0.52360 |
| `left_ankle_roll_joint` | 12 | `left_ankle_roll` | 5 | -0.26180 .. 0.26180 |
| `right_hip_pitch_joint` | 13 | `right_hip_pitch` | 6 | -2.53070 .. 2.87980 |
| `right_hip_roll_joint` | 14 | `right_hip_roll` | 7 | -2.96710 .. 0.52360 |
| `right_hip_yaw_joint` | 15 | `right_hip_yaw` | 8 | -2.75760 .. 2.75760 |
| `right_knee_joint` | 16 | `right_knee` | 9 | -0.08727 .. 2.87980 |
| `right_ankle_pitch_joint` | 17 | `right_ankle_pitch` | 10 | -0.87267 .. 0.52360 |
| `right_ankle_roll_joint` | 18 | `right_ankle_roll` | 11 | -0.26180 .. 0.26180 |
| `waist_yaw_joint` | 19 | `waist_yaw` | 12 | -2.61800 .. 2.61800 |
| `waist_roll_joint` | 20 | `waist_roll` | 13 | -0.52000 .. 0.52000 |
| `waist_pitch_joint` | 21 | `waist_pitch` | 14 | -0.52000 .. 0.52000 |
| `left_shoulder_pitch_joint` | 22 | `left_shoulder_pitch` | 15 | -3.08920 .. 2.67040 |
| `left_shoulder_roll_joint` | 23 | `left_shoulder_roll` | 16 | -1.58820 .. 2.25150 |
| `left_shoulder_yaw_joint` | 24 | `left_shoulder_yaw` | 17 | -2.61800 .. 2.61800 |
| `left_elbow_joint` | 25 | `left_elbow` | 18 | -1.04720 .. 2.09440 |
| `left_wrist_roll_joint` | 26 | `left_wrist_roll` | 19 | -1.97222 .. 1.97222 |
| `left_wrist_pitch_joint` | 27 | `left_wrist_pitch` | 20 | -1.61443 .. 1.61443 |
| `left_wrist_yaw_joint` | 28 | `left_wrist_yaw` | 21 | -1.61443 .. 1.61443 |
| `right_shoulder_pitch_joint` | 29 | `right_shoulder_pitch` | 22 | -3.08920 .. 2.67040 |
| `right_shoulder_roll_joint` | 30 | `right_shoulder_roll` | 23 | -2.25150 .. 1.58820 |
| `right_shoulder_yaw_joint` | 31 | `right_shoulder_yaw` | 24 | -2.61800 .. 2.61800 |
| `right_elbow_joint` | 32 | `right_elbow` | 25 | -1.04720 .. 2.09440 |
| `right_wrist_roll_joint` | 33 | `right_wrist_roll` | 26 | -1.97222 .. 1.97222 |
| `right_wrist_pitch_joint` | 34 | `right_wrist_pitch` | 27 | -1.61443 .. 1.61443 |
| `right_wrist_yaw_joint` | 35 | `right_wrist_yaw` | 28 | -1.61443 .. 1.61443 |

El modelo no contiene joints `finger`, `thumb`, `index`, `middle`, `ring` ni
`pinky`. Las manos son las mallas rígidas `left_rubber_hand` y
`right_rubber_hand`. Por eso `PULGAR_ARRIBA` y `FINGER_GUNS_BANG_BANG` usan una
pose aproximada de brazo/muñeca; no simulan dedos que el MJCF no tiene.

## Saludo existente

El flujo era `Robot.saludar -> ClienteLocal.WaveHand -> orden gesto/saludo ->
Mundo.gesto("saludo")`. El mundo guardaba `accion="saludo"`, pero los dos
visores sólo reaccionaban a `saludando` o `besando`; por eso podía registrarse
sin movimiento visible. Los visores ahora reconocen tanto los nombres actuales
(`saludo`, `dar_la_mano`) como los legados.

## Arquitectura de emotes

- `EmoteManager` y `SimuladorEmotes` sólo manejan nombres semánticos.
- El comando `emote_simulado` existe únicamente en el socket local. No existe
  en el transporte DDS ni se agrega a la lista blanca del robot físico.
- `Mundo` guarda nombre, duración y progreso; no conoce MuJoCo.
- `AnimadorEmotesG1` resuelve cada dirección de `qpos` con
  `mj_name2id`/`jnt_qposadr`, valida tipo y rango, e interpola con `smoothstep`.
- Sólo se permiten los 3 joints de torso y los 14 de brazos/muñecas. Root y
  piernas no están en la lista escribible.
- Todas las curvas empiezan y terminan en neutral y validan un máximo de
  5.2 rad/s. Cada frame parte de la pose base neutral.
- La pose de cielo forma una V separada; la de brazos cruzados usa keyframes
  intermedios para que los brazos no se atraviesen durante la entrada o salida.
- Finger guns tiene preparación, tres extensiones y dos retrocesos. El baile
  alterna tres ciclos y todas las poses muestreadas quedan libres de contactos.
- `StopMove`/`DETENERSE`, otro movimiento o una excepción cancelan el emote.
  La aplicación usa `try/finally` para restaurar neutral si falla un frame.

Los emotes siguen deshabilitados para robot real mientras no se confirmen la
variante, manos, firmware, SDK, telemetría y acciones oficiales disponibles.
