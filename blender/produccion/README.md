# Producción Blender en GPU (Vast.ai) · apartamento 102

> **Propuesta de redistribución conceptual** del apartamento 102: no es planta verificada ni aprobada.

Scripts que se ejecutaron en la instancia Vast.ai `C.59621459` (RTX 4080, Blender 5.2.3, Cycles + OptiX) entre el 7 y el
8 de noviembre de 2026, más las herramientas de análisis usadas para decidir cada cambio. Son las versiones exactas que
corrieron (idénticas byte a byte a las del respaldo verificado).

| Carpeta | Contenido |
|---|---|
| [`v4/`](v4/README.md) | V4 fotorrealista, V4.1 (calibraciones y versión final) y pruebas de iluminación V4.2 |
| [`rediseno_sala/`](rediseno_sala/README.md) | Rediseño de la sala (sofá, obra de arte, mueble TV): v1 ejecutada y v2 preparada sin ejecutar |
| [`herramientas/`](herramientas/README.md) | Análisis de solo lectura: escena, dependencias, comparación de `.blend`, sol y aberturas, calibración de tela |
| `manifiestos/` | SHA-256 del respaldo completo de la instancia (186 archivos + 3 archivos de restauración) |

## Dónde están las escenas y los renders

Los `.blend` y las imágenes **no** están en Git (≈ 80 MB por escena). Están en:

- Mac: `~/Downloads/ora-vast-respaldo-C59621459-2026-11-08/workspace/ora_restore_4080/proyecto_ora/paquete/`
  (verificar con `shasum -a 256 -c RESPALDO_paquete.sha256` desde `proyecto_ora/`; copia del manifiesto en `manifiestos/`).
- Instancia Vast `C.59621459` (detenida, disco conservado), misma ruta bajo `/workspace/`.

Las 18 escenas son autocontenidas: texturas empaquetadas, sin librerías enlazadas ni archivos externos.

## Cómo se ejecutan

Todas las rutas son relativas a la raíz del paquete (`.../proyecto_ora/paquete`), donde estos scripts vivían en `v4/` y
`rediseno_sala/`. Para reproducir, copie la carpeta correspondiente a esa ubicación y lance Blender en segundo plano:

```bash
/workspace/blender-5.2.3-linux-x64/blender -b <escena_fuente.blend> --python <script.py> -- <argumentos>
```

Reglas que cumplen todos los scripts:

- **Nunca escriben la escena fuente**: guardan copias nuevas con `save_as_mainfile(copy=True)`.
- **No tocan geometría arquitectónica, vanos, dimensiones ni distribución**; el rediseño de sala solo sustituye mobiliario
  dentro de su huella aprobada (`apartamento-102/data/propuesta-102.json`).
- Antes y después de cada ejecución se compararon los SHA-256 de escenas y renders anteriores (todos intactos).
- Un solo trabajo de GPU a la vez (ver `docs/coordinacion-claude-codex.md`, regla del `ora.lock`).
