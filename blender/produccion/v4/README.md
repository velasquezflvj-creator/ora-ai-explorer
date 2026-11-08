# V4 · V4.1 · V4.2 — imagen hero `c01_sala_sofa`

Todas las imágenes usan la pose y el campo de visión (75°) de la vista de control `c01_sala_sofa` de la V3
(`datos/prueba_visual_v3_4080/control.json`). Salidas en `datos/prueba_visual_v4_4080/hero/`.

| Script | Fuente → copia | Qué hace | Estado |
|---|---|---|---|
| `v4_fotorrealista.py` | `escena/escena_splat_v2.blend` → `v4/escena_v4.blend` | Albedos neutros realistas (muros 0,88 → 0,66…), madera y travertino a escala real con variación por objeto, sheen en textiles, metales, focos 14 W/4200 K → 9 W/3600 K, emisivos atenuados, calibración automática de exposición y balance; render 1920×1080 | Aprobados los avances técnicos; quedó gris/lila (balance 3885 K) |
| `v4_1_calibracion.py` | `v4/escena_v4.blend` → `v4/escena_v4_1.blend` | Calibración por máscaras de material hacia paleta HEX (muro `#E7E3DB`, techo `#F0EEEA`, sofá `#C8BEB0`, roble natural) | **Descartada**: 4 intentos (sobreexposición, madera naranja, imagen lavada); se conserva la última versión del script |
| `v4_1_final.py` | `v4/escena_v4.blend` → `v4/escena_v4_1.blend` | Orden de ejecución V4.1: balance 4600 K evaluado por neutros, exposición +2,447 EV (límite «no lavada»), travertino mineral (saturación 0,5, mezcla de veta 0,35, poros 0,35); máximo 3 pruebas pequeñas | **V4.1 entregada** (58 s en 4080) |
| `v4_2.py` | `v4/escena_v4_1.blend` → `v4/escena_v4_2.blend` | `prueba`: activa `Sol_HDRI` (18°, entra perpendicular por la puerta-ventana de la sala), exposición +2,0. `final`: render 1920×1080 (no ejecutado) | Prueba 1 960×540 |
| `v4_2_prueba2.py` | `v4/escena_v4_2.blend` → `v4/escena_v4_2_prueba2.blend` | Único cambio pedido: `Fondo.001` 1,2 → 0,8 | **Sin efecto**: `Fondo.001` es solo el fondo visto por ventanas; la luz ambiental real es `Fondo` |
| `v4_2_prueba3.py` | `v4/escena_v4_2.blend` → `v4/escena_v4_2_prueba3.blend` | Dirección aprobada desde la referencia visual: sol a 85° (≈ 6 % del sofá), luz ambiental real `Fondo` 1,0 → 0,6, sofá (sheen 0,2, bouclé ×2, normales ×0,5), travertino estirado 1,0/2,5, exposición en vista | Prueba 3 960×540; pendiente: sol 3800 K y `Fondo` 0,35 |

| `v4_2_final.py` (C4) | `v4/escena_v4_2_prueba3.blend` → `v4/escena_v4_2_final.blend` | Luz V4.2 definitiva desde el módulo común `../comun/luz_v42.py`: sol existente a 3800 K (18°/85°, energía 4 sin cambio) y luz ambiental real `Fondo` 0,6 → 0,35; exposición calibrada solo en la vista (mediana 0,50–0,55, quemado ≤ 1 %). Modos `prueba` (960×540), `final` (1920×1080) y `sin-render` (CPU) | **Preparado; verificado en CPU** (`sin-render`). Pendiente: revisión X1 y aprobación de GPU |

## C4 en Vast.ai (cuando se apruebe)

```bash
tools/vast/sesion.sh subir && tools/vast/sesion.sh preflight
tools/vast/sesion.sh ejecutar --agente claude --escena v4/escena_v4_2_prueba3.blend --script v4/v4_2_final.py --confirmar -- \
  prueba $PAQ/datos/prueba_visual_v4_4080/hero/c01_sala_sofa_v4_2_final_960.png $PAQ/v4/escena_v4_2_final.blend $PAQ/datos/prueba_visual_v4_4080/hero/c01_sala_sofa_v4_2_final_prueba.json
# tras aprobar la prueba:
tools/vast/sesion.sh ejecutar --agente claude --escena v4/escena_v4_2_final.blend --script v4/v4_2_final.py --confirmar -- \
  final $PAQ/datos/prueba_visual_v4_4080/hero/c01_sala_sofa_v4_2.png $PAQ/datos/prueba_visual_v4_4080/hero/c01_sala_sofa_v4_2_final.json
tools/vast/sesion.sh cerrar datos/prueba_visual_v4_4080/hero v4/escena_v4_2_final.blend
```
(`$PAQ` = `/workspace/ora_restore_4080/proyecto_ora/paquete`.)

## Datos

- `datos/mascaras_c01_sala_sofa_480x270.npz`: máscaras de muro, techo, sofá y madera (render de emisión plana) usadas por
  `v4_1_final.py`, `v4_2_prueba2.py` y las herramientas de medición. En la instancia se tomaban de
  `datos/prueba_visual_v4_4080/hero/v4_1_intento4_descartado/`.

## Comandos usados (desde la raíz del paquete)

```bash
B=/workspace/blender-5.2.3-linux-x64/blender; H=datos/prueba_visual_v4_4080/hero
$B -b escena/escena_splat_v2.blend --python v4/v4_fotorrealista.py -- datos/prueba_visual_v3_4080/control.json c01_sala_sofa $PWD/$H/c01_sala_sofa_v4.png $PWD/v4/escena_v4.blend 1024 1920 1080
$B -b v4/escena_v4.blend --python v4/v4_1_final.py -- datos/prueba_visual_v3_4080/control.json <mascaras.npz> $PWD/$H/c01_sala_sofa_v4_1.png $PWD/v4/escena_v4_1.blend
$B -b v4/escena_v4_1.blend --python v4/v4_2.py -- prueba $PWD/$H/c01_sala_sofa_v4_2_prueba_960.png $PWD/v4/escena_v4_2.blend $PWD/$H/c01_sala_sofa_v4_2_parametros.json
$B -b v4/escena_v4_2.blend --python v4/v4_2_prueba2.py -- $PWD/$H/c01_sala_sofa_v4_2_prueba2_960.png $PWD/v4/escena_v4_2_prueba2.blend $PWD/$H/c01_sala_sofa_v4_2_prueba2_parametros.json <mascaras.npz>
$B -b v4/escena_v4_2.blend --python v4/v4_2_prueba3.py -- $PWD/$H/c01_sala_sofa_v4_2_prueba3_960.png $PWD/v4/escena_v4_2_prueba3.blend $PWD/$H/c01_sala_sofa_v4_2_prueba3_parametros.json <mascaras.npz>
```

Cada ejecución deja un JSON de parámetros (`*_parametros.json` / `*_cambios.json`) con valores anteriores y nuevos; copias
en `apartamento-102/capturas/v4-fotorrealista/` (fuera de Git).
