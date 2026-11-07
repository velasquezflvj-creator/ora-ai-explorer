# Recursos web generados desde Blender (recorridos V2 y V3 del apartamento 102)

Archivos derivados que usan `tools/build_recorrido.mjs` (V2) y `tools/build_recorrido_v3.mjs` (V3). Se versionan
para que el visor se pueda compilar sin Blender; se regeneran con los scripts de `blender/scripts/` (ver
`blender/README.md` y `docs/pipeline-apartamentos.md`).

| Carpeta | Contenido | Generado con | Origen y licencia |
| --- | --- | --- | --- |
| `texturas/` | Travertino, enchape, roble, relieve de yeso, lino y bouclé (1024 px) y piso de 120 × 60 horneado (2048 px, periódico de 4,8 m); `escala.json` = tamaño real en metros | `exportar_web.py` | Derivadas de texturas **CC0** de Poly Haven (marble_01 no se usa; oak_veneer_01, beige_wall_001, rough_linen, wool_boucle) y ambientCG (Travertine009, Tiles139) |
| `sondas/` | 10 panoramas HDR 360° (512 × 256) del interior, uno por espacio, con la gradación del render V3 (+0,8 EV, 5000 K) | `exportar_web.py` | Render propio (Cycles) de la escena V3; el exterior proviene del HDRI CC0 green_point_park (Poly Haven) |
| `horneado/` | `piso_luz.hdr` (irradiancia del piso) y `cielo.hdr` (apariencia del cielo raso), 1024 × 1024, vista cenital ortográfica | `hornear_planos_web.py` | Render propio (Cycles) de la escena V3 |

El modelo (`../apto-102-propuesta.glb`) no se modifica: las coordenadas de planta para la luz horneada se calculan en
el visor. Propuesta de redistribución conceptual: no es planta verificada ni aprobada.
