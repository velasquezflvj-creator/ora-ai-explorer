# Coordinación Claude + Codex · ORA AI Explorer (apartamento 102)

> Propuesta de redistribución conceptual del apartamento 102: no es planta verificada ni aprobada. Este plan organiza el
> trabajo; no autoriza publicar, contratar ni renderizar. Cada paso marcado **[aprobación]** espera la confirmación del usuario.

## 1. Estado de partida (8 nov 2026)

| Pieza | Dónde está | Estado |
|---|---|---|
| Código web (V1–V5, piloto splat) | Mac, rama local `feat/apto-102-splat-piloto` (commit `acb4dc2`) | Ramas V3–V5 y piloto **solo locales**; en GitHub solo `main` y `feat/apartamento-102-rediseno` |
| Escenas Blender V4 → V4.2 y rediseño de sala | Mac: `~/Downloads/ora-vast-respaldo-C59621459-2026-11-08/` (respaldo verificado SHA-256) · Vast detenida | 18 `.blend` autocontenidos (texturas empaquetadas, sin enlaces externos) |
| Scripts de producción (V4, V4.1, V4.2, sala) | Respaldo de Vast (`paquete/v4/*.py`, `paquete/rediseno_sala/*.py`) y `apartamento-102/capturas/` | Fuera del repositorio |
| Pipeline V3 de Codex (Jupyter) | `tools/produccion_visual_v3/` | Sin seguimiento en Git |
| Entregables visuales | `apartamento-102/capturas/v4-fotorrealista/`, `capturas/rediseno-sala/` | Sin seguimiento en Git |
| Blender local | `/Volumes/Blender/Blender.app` (5.2.3) + MCP de Blender | Codex: solo consulta; Claude: procesos en segundo plano |

## 2. Reglas comunes

1. **GitHub es la única fuente de código.** Scripts de Blender, runners de Jupyter, configuración y manifiestos van al repositorio; los `.blend`, renders y paquetes no (se guardan en el Mac y en Vast, y en Git solo su manifiesto SHA-256). Git LFS queda como opción si se decide versionar binarios.
2. **Una rama por tarea**, nombrada `agente/tema` (`claude/sala-v2`, `codex/runner-jupyter`). Cada agente revisa el PR del otro; **el usuario fusiona**. Ningún agente publica ni hace push sin autorización **[aprobación]**.
3. **Archivos maestros y versiones aprobadas son de solo lectura**: `blender/*.blend`, V4, V5, `v4/escena_v4*.blend`. Todo trabajo nuevo crea una copia con sufijo de versión y se verifica por hash antes/después.
4. **Un solo trabajo de GPU a la vez.** Antes de usar la RTX, el agente crea `/workspace/ora.lock` con su nombre, tarea y hora; si existe, espera. Se borra al terminar.
5. **Ninguna sesión de Vast termina sin respaldo verificado en el Mac** (rsync + `sha256sum -c`) y la instancia se **detiene** (no se destruye) al acabar.
6. **Blender MCP**: inspección y capturas desde la sesión GUI del Mac; nadie guarda la escena abierta en la GUI.

## 3. Reparto de roles

| | Claude | Codex |
|---|---|---|
| Blender / escenas | Iluminación, materiales, mobiliario, simulaciones, render de prueba y métricas | Auditoría de nodos y escenas con MCP (solo lectura); revisión de scripts |
| Vast.ai | Sesiones de GPU por SSH, sincronización, cierre y registro de costo | Runners pegables en Jupyter (mismo script, mismo resultado) |
| Web / recorrido | Exportación de luz horneada y assets desde Blender | Integración en three.js / Spark, pruebas automatizadas, rendimiento |
| Repositorio | Scripts de producción + manifiestos | Estructura, pruebas, CI local, documentación técnica |

## 4. Protocolo de una sesión de GPU

1. **[aprobación]** El usuario inicia la instancia en Vast.
2. Sincronizar código: `rsync` del repositorio (o `git pull` si se configura una deploy key de solo lectura **[aprobación]**).
3. Preflight: hashes de escenas fuente, GPU libre, `ora.lock` libre, espacio en disco.
4. Ejecutar la tarea (pruebas pequeñas primero; render final solo con aprobación).
5. Traer resultados al Mac con manifiesto y verificarlos.
6. Detener la instancia (`vastai stop instance $CONTAINER_ID --api-key $CONTAINER_API_KEY` desde dentro) y anotar tiempo y costo en `docs/registro-gpu.md`.

## 5. Tareas concretas del próximo avance

**Estado al 8 nov 2026 (rama `claude/produccion-blender`, sin publicar todavía):**
C1 ✅ hecho · C2 ✅ hecho (probado en simulación; falta la primera sesión real) · C3 preparado y verificado en CPU (tres fallos
corregidos antes de usar la GPU; pendiente de aprobación y revisión X1) · C4 pendiente de aprobación ·
`AGENTS.md` en la raíz para Codex · pruebas nuevas: `tests/vast-sesion.test.cjs` (8) y `tests/produccion-blender.test.cjs` (4).
Bloqueo: publicar las ramas requiere que el usuario autentique Git en este Mac.

### Claude
- **C1 · Scripts al repositorio.** Mover los scripts de V4, V4.1, V4.2 y del rediseño a `blender/produccion/` con un README por versión y el manifiesto del respaldo. Rama `claude/produccion-blender`.
- **C2 · `tools/vast/sesion.sh`.** Un solo comando para: sincronizar, preflight, lock, traer resultados con SHA-256 y detener la instancia.
- **C3 · Sala V2** (tras aprobación): simulación de tela calibrada (tensión 80 + resortes internos), cuadro 4K con relieve real, refinamiento del mueble TV, dos focos reorientados y **una** vista de control 1280×720. Script ya preparado: `capturas/rediseno-sala/borrador_v2_no_ejecutado/rediseno_sala_v2.py`.
- **C4 · Luz V4.2 definitiva** (tras aprobación): sol 3800 K y luz ambiental real (`Fondo`) 0,35; una prueba 960×540 y el render final solo si se aprueba.

### Codex
- **X1 · Revisión de C1/C3** antes de cualquier ejecución en GPU: lógica, rutas, protección de maestros y escritura solo en copias.
- **X2 · Runner Jupyter para C3/C4** con el mismo patrón de `tools/produccion_visual_v3/` (pegar y ejecutar), incluido el preflight y `ora.lock`.
- **X3 · Auditoría con Blender MCP** de `escena_sala_rediseno_v1.blend` (solo lectura): inventario de materiales, densidad de malla, objetos fuera de huella.
- **X4 · Recorrido web**: preparar en el visor V5 una ruta de carga para el mobiliario nuevo (GLB exportado) y la luz horneada de V4.2, con pruebas que garanticen que V4 y V5 no cambian.
- **X5 · Orden del repositorio**: incorporar `tools/produccion_visual_v3/` (sin `__pycache__` ni zip) y `.gitignore` para capturas y binarios.

### Usuario
- Aprobar la dirección de la sala V2 y la luz V4.2.
- Autorizar el push de las ramas locales (V3–V5, piloto) y de las ramas de trabajo.
- Iniciar/detener Vast cuando se necesite GPU (o autorizar a los agentes a detenerla al terminar).

## 6. Hacia el recorrido 3D fotorrealista

1. Cerrar sala (C3) y luz (C4) → escena V4.2 aprobada.
2. Hornear luz y exportar mobiliario/arte desde esa escena en Vast (Claude) → assets web.
3. Integrarlos en el visor sobre la V5 (Codex), medir fps y calidad con las pruebas existentes.
4. Opcional: piloto de Gaussian Splatting con la escena aprobada (paquete y scripts ya listos).
