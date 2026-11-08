# Estado del proyecto · cierre del 8 nov 2026

Apartamento 102: propuesta de redistribución conceptual (no planta verificada ni aprobada).

## Dónde está cada cosa

| Elemento | Ubicación | Estado |
|---|---|---|
| Código y documentación | Rama local `claude/produccion-blender` (sobre `feat/apto-102-splat-piloto`) | Commits locales; **sin publicar** (falta autenticación de Git en el Mac) |
| Ramas de desarrollo a publicar | `feat/apto-102-recorrido-interactivo`, `-v3`, `-v4`, `-v5`, `feat/apto-102-splat-piloto`, `claude/produccion-blender` | Revisadas: 85,6 MB nuevos, mayor archivo 15,1 MB, sin credenciales |
| Escenas `.blend`, renders, registros de GPU | `~/Downloads/ora-vast-respaldo-C59621459-2026-11-08/` | 186 + 3 archivos verificados por SHA-256; 18 escenas autocontenidas |
| Instancia Vast.ai `C.59621459` (RTX 4080) | Detenida (no destruida), disco conservado | Solo almacenamiento ≈ 0,009 USD/h; ver `docs/registro-gpu.md` |
| Archivos maestros (`blender/*.blend`, GLB original) | Sin cambios | Hashes en `tools/splat/maestros.sha256` |
| Entregables visuales | `apartamento-102/capturas/v4-fotorrealista/`, `apartamento-102/capturas/rediseno-sala/` | Fuera de Git (binarios) |

## Hecho en esta jornada

- V4, V4.1 (entregada) y pruebas V4.2 de iluminación; diagnóstico de la luz ambiental real (`Fondo`, no `Fondo.001`).
- Rediseño de sala v1 (sofá escultórico, obra de arte, mueble TV) con tres vistas previas; v2 preparado.
- C1: scripts de producción y herramientas en `blender/produccion/` (idénticos al respaldo).
- C2: `tools/vast/sesion.sh` (sesión de GPU con bloqueo, respaldo verificado y parada segura).
- `AGENTS.md` para Codex; plan conjunto en `docs/coordinacion-claude-codex.md`.
- Pruebas nuevas sin GPU: `tests/vast-sesion.test.cjs` (8) y `tests/produccion-blender.test.cjs` (4). La prueba en seco
  encontró y permitió corregir tres fallos del script V2 antes de gastar GPU.

## Pendiente (en orden)

1. **Usuario**: autenticar Git en el Mac y publicar las seis ramas:
   `git push -u origin feat/apto-102-recorrido-interactivo feat/apto-102-recorrido-v3 feat/apto-102-recorrido-v4 feat/apto-102-recorrido-v5 feat/apto-102-splat-piloto claude/produccion-blender`
2. **Codex X1**: revisar `blender/produccion/rediseno_sala/rediseno_sala_v2_no_ejecutado.py` y `tools/vast/sesion.sh`.
3. **Usuario**: aprobar la ejecución de C3 (sala V2) y C4 (luz V4.2 definitiva) en GPU.
4. **Codex X2–X5**: runner Jupyter, auditoría MCP, integración web, orden del repositorio.
5. Decidir si se destruye la instancia detenida (el respaldo completo ya está en el Mac) para eliminar el costo de almacenamiento.
