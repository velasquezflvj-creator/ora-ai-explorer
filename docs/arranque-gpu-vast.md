# Arranque de la GPU remota (Vast.ai) · procedimiento para mañana

Apartamento 102: propuesta de redistribución conceptual (no planta verificada). Todo el trabajo pesado (Blender, simulaciones,
renders) se hace en la RTX 4080 remota; el Mac solo edita código, sincroniza y revisa imágenes.

## Estado al cerrar (8 nov 2026)

| Pieza | Estado |
|---|---|
| Instancia `C.59621459` (RTX 4080, 24 núcleos, 31 GB RAM) | **Detenida, no destruida** (SSH rechaza la conexión); disco conservado. Solo cobra almacenamiento ≈ 0,009 USD/h |
| Contenido del disco remoto | Igual que el respaldo del Mac: `paquete/` con escenas V4–V4.2 y sala v1, Blender 5.2.3 en `/workspace/blender-5.2.3-linux-x64/` |
| Respaldo en el Mac | `~/Downloads/ora-vast-respaldo-C59621459-2026-11-08/` · re-verificado hoy: 186/186 + 3/3 SHA-256 |
| Código | GitHub: `claude/produccion-blender` (`cf42ab0`), `claude/c3-c4` (C4 publicado en `e0d4607` + arranque de esta nota) |
| Llaves en el Mac | `~/.ssh/vast_59585596` (instancia) · `~/.ssh/github_ora` (publicar en GitHub; solo este repositorio) |
| Herramientas del Mac | `git`, `rsync`, `node` 24, `ssh`. **No hace falta instalar nada** |

Riesgo conocido: al reanudar, la RTX 4080 de esa máquina puede estar alquilada por otro cliente. El disco se conserva igual; si
no hay GPU libre, esperar o crear otra instancia y subir el respaldo del Mac (≈ 2 GB, ~25 min a la velocidad medida).

## 1. Encender (usuario)

En la consola de Vast.ai → **Instances** → `C.59621459` → **Start**. Cuando esté en *Running*, pulse **Connect** y copie la
línea SSH (`ssh -p PUERTO root@IP …`). La IP y el puerto **cambian** en cada arranque.

## 2. Conectar (un comando, desde el worktree de Claude o desde el repositorio)

```bash
tools/vast/sesion.sh configurar 'ssh -p PUERTO root@IP'   # escribe tools/vast/vast.env (ignorado por Git)
tools/vast/sesion.sh estado                               # GPU, bloqueo, disco, Blender y USD/h
```

La primera conexión acepta la clave del host nuevo (`accept-new`) y la recuerda; si después cambiara, la conexión se rechaza.

## 3. Subir código y comprobar

```bash
tools/vast/sesion.sh subir        # commit actual → paquete/_codigo/<rama>-<commit>/ (inmutable)
tools/vast/sesion.sh preflight    # GPU libre, ora.lock libre, disco, Blender 5.2.3, escenas protegidas intactas
```

`subir` solo acepta código con commit. Para combinar trabajo de Claude y Codex (p. ej. la corrección de `traer` de Codex,
`01b9596`, que vive en su rama local `codex/x1-seguridad`), el usuario decide la rama de integración antes de subir.

## 4. Trabajos de GPU previstos (uno a la vez; el bloqueo `ora.lock` lo garantiza)

`$PAQ` = `/workspace/ora_restore_4080/proyecto_ora/paquete`. Sin `--confirmar`, `ejecutar` solo muestra el plan.

| Orden | Trabajo | Comando |
|---|---|---|
| 1 | **C4 prueba** (960×540) | `tools/vast/sesion.sh ejecutar --agente claude --escena v4/escena_v4_2_prueba3.blend --script v4/v4_2_final.py --confirmar -- prueba $PAQ/datos/prueba_visual_v4_4080/hero/c01_sala_sofa_v4_2_final_960.png $PAQ/v4/escena_v4_2_final.blend $PAQ/datos/prueba_visual_v4_4080/hero/c01_sala_sofa_v4_2_final_prueba.json` |
| 2 | **C4 final** 1920×1080 (tras aprobar la prueba) | `… --escena v4/escena_v4_2_final.blend --script v4/v4_2_final.py --confirmar -- final $PAQ/datos/prueba_visual_v4_4080/hero/c01_sala_sofa_v4_2.png $PAQ/datos/prueba_visual_v4_4080/hero/c01_sala_sofa_v4_2_final.json` |
| 3 | **C3 calibración de cojines** en la CPU remota (sin render) | `… --escena rediseno_sala/escena_sala_rediseno_v1.blend --script rediseno_sala/rediseno_sala_v2_no_ejecutado.py --confirmar -- $PAQ/rediseno_sala/escena_sala_rediseno_v2.blend $PAQ/datos/rediseno_sala/control --sin-render` |
| 4 | **C3 vista de control** 1280×720 (tras aceptar los cojines) | igual que 3, sin `--sin-render` |

Estado de C3 (pruebas en CPU del Mac): asiento **aceptado** (volumen 89 %, asentamiento 4,7 cm); respaldos y decorativos
todavía rechazados por el control de calidad (empiezan intersecando asiento y concha; la separación actual solo avanza en X:
falta también elevarlos). El script es seguro: un cojín rechazado conserva su forma original. La calibración restante se
hace en el paso 3, en la CPU de 24 núcleos de la instancia (cada cojín ~15–50 s en el Mac).

## 5. Traer y apagar (siempre)

```bash
tools/vast/sesion.sh cerrar datos/prueba_visual_v4_4080/hero datos/rediseno_sala v4/escena_v4_2_final.blend rediseno_sala
```

Trae sin sobrescribir a `~/Downloads/ora-vast-respaldo/<fecha>/`, verifica SHA-256, **detiene** (no destruye) la instancia,
comprueba que dejó de responder y anota duración y costo en `docs/registro-gpu.md`. Si la verificación falla, no detiene.

## Trabajo simultáneo de Claude y Codex

- Cada agente en su carpeta de trabajo: Codex en el repositorio principal (`codex/*`), Claude en
  `.claude/worktrees/c3-c4` (`claude/c3-c4`). Nunca dos agentes en la misma carpeta.
- Ambos pueden programar y probar en el Mac a la vez; **la GPU la usa un solo trabajo** (`ora.lock` indica quién la tiene).
- En el Mac, para no cargarlo mientras trabaja la GPU: `ORA_SIN_BLENDER_LOCAL=1 npm test` omite las pruebas que abren
  Blender local. Ninguna tarea prevista requiere renders ni simulaciones en el Mac.
