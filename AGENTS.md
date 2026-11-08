# Instrucciones para agentes (Codex, Claude)

ORA AI Explorer: explorador web de apartamentos. El trabajo actual es el **apartamento 102**, una **propuesta de
redistribución conceptual: no es planta verificada ni aprobada**. Todos los rótulos de «propuesta» deben conservarse.

El plan de trabajo conjunto y el reparto de tareas están en [`docs/coordinacion-claude-codex.md`](docs/coordinacion-claude-codex.md).
Las tareas de Codex son X1–X5; las de Claude, C1–C4.

## Estructura

| Ruta | Contenido |
|---|---|
| `index.html`, `server.mjs`, `js/`, `css/` | Explorador web (servidor estático: `npm start`, puerto 8768 por defecto) |
| `apartamento-102/` | Recorridos 3D del 102 (V1–V5, piloto de Gaussian Splatting), datos de la propuesta (`data/propuesta-102.json`) |
| `apartamento-102/src/`, `apartamento-102/tools/` | Fuentes de los recorridos (three.js) y scripts de compilación (esbuild) |
| `blender/scripts/` | Pipeline Blender de los recorridos (exportación, horneado, splat) |
| `blender/produccion/` | Scripts que se ejecutaron en GPU (V4–V4.2, rediseño de sala) y herramientas de análisis; ver su README |
| `tools/vast/` | `sesion.sh`: sesión de GPU en Vast.ai (subir, preflight, ejecutar con bloqueo, traer con SHA-256, detener) |
| `tools/splat/`, `nube/splat/` | Piloto de Gaussian Splatting (paquete y scripts para la nube) |
| `tests/*.test.cjs` | Pruebas `node:test` (algunas usan Playwright/Chromium) |
| `docs/` | Documentación (coordinación, registro de GPU, fidelidad visual, splat) |

## Comandos

```bash
npm test                                         # todas las pruebas
node --test tests/vast-sesion.test.cjs           # una prueba concreta
node --test tests/produccion-blender.test.cjs
tools/vast/sesion.sh ayuda
```

Blender local: `/Volumes/Blender/Blender.app/Contents/MacOS/Blender` (5.2.3), siempre en segundo plano (`-b`).

## Reglas que no se negocian

1. **Archivos maestros de solo lectura**: `blender/*.blend` (Master, V3, Video) y el GLB `apartamento-102/modelo/apto-102-propuesta.glb`.
   Sus SHA-256 están en `tools/splat/maestros.sha256`; ninguna tarea los abre para escribir.
2. **Versiones aprobadas intactas**: V4 y V5 (las pruebas `recorrido-v4-102` y `recorrido-v5-102` lo comprueban), y las escenas
   `v4/escena_v4*.blend` del respaldo. Todo trabajo nuevo crea una copia con sufijo de versión.
3. **No tocar `main` ni publicar sin autorización del usuario**: una rama por tarea (`codex/<tema>`, `claude/<tema>`),
   sin merge ni pull request salvo que el usuario lo pida. El usuario fusiona.
4. **No cambiar arquitectura**: distribución, dimensiones, muros, puertas y ventanas se conservan; el mobiliario nuevo
   respeta su huella en `propuesta-102.json`.
5. **GPU / gastos**: ningún render, simulación o instancia de pago sin aprobación. Un solo trabajo de GPU a la vez:
   `/workspace/ora.lock` (lo gestiona `tools/vast/sesion.sh`). Ninguna sesión termina sin `traer` verificado y `detener`.
6. **Blender MCP**: Codex lo usa solo para consulta e inspección de la sesión GUI; nadie guarda la escena abierta en la GUI.
7. **Binarios fuera de Git**: `.blend`, renders y paquetes van al respaldo del Mac; en Git, solo scripts y manifiestos SHA-256.
8. **Respaldos**: `~/Downloads/ora-vast-respaldo-*` y ramas `base/*` y `respaldo/*` son de solo lectura.

## Convenciones

- Código, comentarios, mensajes de commit y documentación en **español**.
- Antes de proponer un cambio, ejecutar las pruebas relacionadas y dejar constancia del resultado.
- Scripts de Blender: `save_as_mainfile(copy=True)` hacia una ruta nueva; nunca `save_mainfile()` sobre la fuente.
- Revisión cruzada: Claude revisa las ramas de Codex y viceversa antes de usar la GPU.
