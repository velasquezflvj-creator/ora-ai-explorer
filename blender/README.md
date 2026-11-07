# Blender · apartamento 102

Carpeta de trabajo de Blender. **Solo `scripts/` y este README están en Git**; los `.blend`, renders y recursos
descargados son grandes y se regeneran con los scripts (o se conservan localmente).

| Archivo | Qué es | ¿Se modifica? |
| --- | --- | --- |
| `Apartamento_102_Render_Master.blend` | Primera versión (importación, materiales, luces, cámara de prueba) | No: versión de referencia |
| `Apartamento_102_Render_V3.blend` | Fase 3 fotorrealista (render `render/Apartamento_102_Fotorrealista_V3.png`) | No: base del video y de la exportación web |
| `Apartamento_102_Video.blend` | Copia de V3 con la cámara `CAM_Video` (9 tomas, 53 s) | Se regenera con `scripts/camara_video.py` |
| `recursos/` | Copia de los recursos del proyecto + `descargas/` (texturas y HDRI CC0, ver `descargas/CREDITOS.md`) | Solo lectura |
| `render/` | Renders, comparaciones, vista previa del video y cuadros de muestra | Salidas |

## Scripts (`scripts/`)

```bash
B="/Applications/Blender.app/Contents/MacOS/Blender"   # o la ruta de Blender 5.x
# escena de render desde el GLB y la configuración (no toca el GLB)
"$B" -b --factory-startup --python blender/scripts/importar_apartamento.py -- blender/scripts/apto-102.json blender/Apartamento_102_Render_Nuevo.blend
# recursos del visor web: texturas, piso horneado y sondas 360°
"$B" -b blender/Apartamento_102_Render_V3.blend --python blender/scripts/exportar_web.py -- blender/scripts/apto-102.json apartamento-102/modelo/web
# luz horneada del piso y del cielo raso para el recorrido V3 (no guarda el .blend de entrada)
"$B" -b blender/Apartamento_102_Render_V3.blend --python blender/scripts/hornear_planos_web.py -- blender/scripts/apto-102.json apartamento-102/modelo/web/horneado
# atlas de luz de las superficies fijas + copia del GLB con UV de luz (recorrido V4)
"$B" -b blender/Apartamento_102_Render_V3.blend --python blender/scripts/hornear_lightmaps_web.py -- hornear blender/scripts/apto-102.json apartamento-102/modelo/web/v4
"$B" -b --factory-startup --python blender/scripts/hornear_lightmaps_web.py -- exportar blender/scripts/apto-102.json apartamento-102/modelo/web/v4
node apartamento-102/tools/verificar_glb.mjs apartamento-102/modelo/apto-102-propuesta.glb apartamento-102/modelo/web/v4/apto-102-v4.glb
# recorrido cinematográfico: estimación del render final y vista previa EEVEE
"$B" -b blender/Apartamento_102_Render_V3.blend --python blender/scripts/camara_video.py -- blender/scripts/apto-102.json blender/Apartamento_102_Video.blend --estimar 3
"$B" -b blender/Apartamento_102_Video.blend --python blender/scripts/camara_video.py -- blender/scripts/apto-102.json blender/Apartamento_102_Video.blend --vista-previa blender/render/Apartamento_102_Recorrido_previa_640x360.mp4
```

`apto-102.json` reúne todo lo específico del apartamento; el procedimiento para otro apartamento está en
`docs/pipeline-apartamentos.md`.

## Advertencias que se conservan

Cada objeto mantiene sus metadatos del GLB (`verificado`, `categoria`, `fuente`). Los renders llevan el sello
«Propuesta de redistribución conceptual – no es planta verificada ni aprobada. Balcón, acabados, muebles y
exterior ilustrativos». La colección `CTX_Contexto_neutro (no arquitectonico)` (V3) contiene volúmenes grises fuera
de la envolvente para evitar fugas de luz: no representan el corredor ni la torre reales.
