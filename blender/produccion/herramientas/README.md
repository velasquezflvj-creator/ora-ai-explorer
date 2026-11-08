# Herramientas de análisis (solo lectura salvo indicación)

Ninguna guarda la escena que abre. Se usaron para decidir y verificar los cambios de V4 → V4.2 y del rediseño de sala.

| Script | Uso | Para qué sirvió |
|---|---|---|
| `analizar_escena.py` | `blender -b escena.blend --python analizar_escena.py` → `/tmp/ora_v4_analisis.json` | Color, Cycles, mundo, luces, materiales (nodos, imágenes, escalas de mapeo) y rangos UV: diagnóstico de la dominante amarilla y la repetición de texturas |
| `inspeccionar_travertino.py` | `blender -b escena.blend --python inspeccionar_travertino.py` | Árbol de nodos de salpicadero, mesón y piso: por qué el travertino parecía madera |
| `sol_fugas_y_aberturas.py` | `blender -b escena.blend --python sol_fugas_y_aberturas.py` | Dirección real de `Sol_HDRI`, puntos de salida de los rayos solares por la fachada y objetos de fachada (sin fugas a través de sólidos) |
| `sol_busqueda_direcciones.py` | ídem | Barrido elevación × azimut: % de la vista al sol, materiales iluminados y rayos fuera del vano |
| `sol_sobre_sofa_por_pixel.py` | `… -- <mascaras.npz>` | % del sofá visible con sol directo, por píxel (más fiable que la rejilla gruesa) |
| `dependencias_blend.py` | `blender -b --factory-startup x.blend --python dependencias_blend.py` | Imágenes empaquetadas/externas/faltantes, librerías y otros externos (respaldo: 18/18 autocontenidos) |
| `comparar_blend_huella.py` | `blender -b --factory-startup --python comparar_blend_huella.py -- a.blend b.blend salida.json` | Huella de geometría, materiales, imágenes, cámaras, luces, render y colecciones de dos escenas |
| `comparar_blend_propiedades.py` | `… -- a.blend [b.blend …] salida.json` (un proceso por archivo) | Propiedades RNA de escena/render/cycles/vista, selección y objetos |
| `comparar_blend_props_personalizadas.py` | `blender -b x.blend --python … -- salida.json` | Contenido de las propiedades personalizadas (datos de la propuesta) |
| `inspeccionar_sala.py` | `blender -b escena.blend --python inspeccionar_sala.py` | Inventario de la sala y piezas sueltas de `MOB_Sala` por material |
| `calibrar_tela_cojin.py` | `blender -b rediseno_sala/escena_sala_rediseno_v1.blend --python calibrar_tela_cojin.py` | Calibración de la simulación de tela del asiento (no guarda): volumen, hundimiento, estabilidad |

Nota: `sol_fugas_y_aberturas.py` lee la dirección del sol desde `rotation_euler` porque `matrix_world` de una luz oculta
en render no estaba actualizada en segundo plano (un primer análisis la leyó vertical por ese motivo).
