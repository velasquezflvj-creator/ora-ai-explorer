# Procedimiento reutilizable: de un apartamento en GLB a recorrido web y video

Este documento describe cómo se incorporó el apartamento 102 (Blender + visor web) y cómo repetir el proceso
con otro apartamento sin reconstruir el sistema a mano. Es un procedimiento interno, no una plataforma.

## Piezas y responsabilidades

| Paso | Herramienta | Entrada | Salida |
| --- | --- | --- | --- |
| 1. Modelo | `apartamento-NNN/tools/generar_glb.py` (por apartamento) | planta (JSON derivado del DWG) | `modelo/apto-NNN.glb` con nombres `ARQ_ / PRO_ / ILU_ / APA_ / MOB_ / PROP_` y `extras` (verificado, categoría, fuente, huella) |
| 2. Escena de render | `blender/scripts/importar_apartamento.py` | GLB + `blender/scripts/apto-NNN.json` | `.blend` con muebles, materiales PBR, luces 4200 K, portales, cámara de prueba y advertencias |
| 3. Recursos web | `blender/scripts/exportar_web.py` | `.blend` + JSON | `modelo/web/texturas/*.jpg` (claves del visor), piso horneado, `modelo/web/sondas/*.hdr` |
| 4. Visor | `apartamento-NNN/tools/build_recorrido.mjs` | GLB, planta, muebles, `modelo/web` | `dist/recorrido-app.js`, `dist/recorrido-datos.js` |
| 5. Video | `blender/scripts/camara_video.py` | `.blend` + JSON (`video.tomas`) | `.blend` de video, vista previa MP4 y estimación del render final |
| 6. Control | `tests/*.test.cjs`, `tools/medir_rendimiento.mjs`, `tools/capturar_vistas.mjs` | servidor local | pruebas, fps por perfil, capturas comparables con Blender |

Todo lo específico de un apartamento vive en **un JSON** (`blender/scripts/apto-102.json` es la referencia):

- `origen_plano`: traslado del plano local del visor (x este, y norte, origen en la esquina SO) a Blender.
- `importar`: GLB, muebles por clave (`extras.modelo` del nodo) y grupos que el visor oculta por defecto.
- `materiales`: nombre de material del GLB → textura, color, rugosidad, relieve; vidrios y emisivos (K, intensidad).
- `texturas` y `piso`: fuentes CC0, tamaño real en metros, ajustes de color (en espacio lineal) y piso horneado.
- `luces`: HDRI, temperatura y potencia de las luminarias (las posiciones salen de `ILU_Luminarias.extras.puntos`),
  portales sobre los vanos de fachada.
- `sondas`: un punto por espacio, sobre piso libre (fuera de las huellas de `propuesta-NNN.json`).
- `camara_prueba` y `video.tomas`: tomas entre nudos del recorrido validado del visor.

## Para un apartamento nuevo (NNN)

1. Generar `apartamento-NNN/modelo/apto-NNN.glb` con la misma convención de nombres y `extras` que el 102.
   Lo que el visor y los scripts necesitan: `ILU_Luminarias.extras.puntos`, nodos `MOB_*` con `modelo`/`escala`
   para muebles de terceros, `grupo` en cada nodo, y nombres de material estables.
2. Copiar `blender/scripts/apto-102.json` a `apto-NNN.json` y cambiar: `apartamento`, `escena`, `origen_plano`,
   rutas de `importar`, `portales` (coordenadas de los vanos), `sondas.puntos`, `camara_prueba` y `video.tomas`.
3. `Blender -b --factory-startup --python blender/scripts/importar_apartamento.py -- blender/scripts/apto-NNN.json blender/Apartamento_NNN_Render_Master.blend`
4. Revisar en Blender (render de prueba) y ajustar el JSON; repetir el paso 3 si hace falta (no se edita a mano).
5. `Blender -b blender/Apartamento_NNN_Render_Master.blend --python blender/scripts/exportar_web.py -- blender/scripts/apto-NNN.json apartamento-NNN/modelo/web`
6. Copiar `apartamento-102/recorrido.html`, `css/recorrido.css`, `src/app-recorrido.mjs` y `tools/build_recorrido.mjs`
   al nuevo apartamento y ajustar lo que hoy está fijo en el código del 102 (ver «Pendiente de generalizar»).
7. `node apartamento-NNN/tools/build_recorrido.mjs`, `npm test`, `node apartamento-NNN/tools/medir_rendimiento.mjs ...`
8. Video: `camara_video.py ... --estimar 3` y `--vista-previa` antes de decidir un render final.

## Pendiente de generalizar (hoy está fijo en el código del 102)

- En `src/app-recorrido.mjs`: `VIEWS` (puntos de vista por espacio y `entrada`), `LIGHTS` (luces de apoyo del
  visor), `POIS`, capítulos del recorrido (`TOUR_*`) y la lógica del balcón propuesto. Conviene moverlos a
  `data/visor-NNN.json` y que el visor los lea de `DATA`, igual que ya lee la planta.
- `pbr102.mjs` (propuestas de acabados): la tabla debería salir del mismo JSON de materiales que usa Blender, para
  que web y render no se desincronicen. Hoy el JSON de Blender la replica a mano (con su nota de origen).
- El visor comparte `../../apartamento-104/src/acabados.mjs` y `texturas.mjs`: si se crea un tercer apartamento,
  conviene moverlos a una carpeta común (`comun/`).

## Publicación web

El visor es estático (`index.html` / `recorrido.html` + `dist/*.js`): se abre con `node server.mjs` o con doble
clic (file://). Publicar en GitHub Pages es copiar la carpeta tal cual; **no se ha publicado nada** de esta rama.
`dist/recorrido-datos.js` pesa ~20 MB (texturas y sondas en base64): antes de publicar, ver las recomendaciones de
compresión (KTX2 / sondas en RGBM PNG / carga diferida por espacio) en `apartamento-102/RECORRIDO-V2.md`.
