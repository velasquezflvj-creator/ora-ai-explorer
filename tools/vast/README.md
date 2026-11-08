# Sesiones de GPU en Vast.ai

`sesion.sh` encapsula el protocolo de `docs/coordinacion-claude-codex.md`: subir código versionado, comprobar, ejecutar con
bloqueo, traer resultados verificados y detener la instancia. Lo usan igual Claude (por SSH desde el Mac) y Codex.

```bash
tools/vast/sesion.sh configurar 'ssh -p PUERTO root@IP'   # línea «Connect» de Vast: escribe tools/vast/vast.env (IP/puerto cambian en cada inicio)
tools/vast/sesion.sh estado
tools/vast/sesion.sh subir                            # blender/produccion del commit actual → paquete/_codigo/<rama>-<commit>/
tools/vast/sesion.sh preflight
tools/vast/sesion.sh ejecutar --agente claude --escena v4/escena_v4_2.blend --script v4/v4_2.py -- prueba …   # muestra el plan
tools/vast/sesion.sh ejecutar --agente claude --escena … --script … --confirmar -- …                          # solo con aprobación
tools/vast/sesion.sh cerrar datos/prueba_visual_v4_4080/hero rediseno_sala                                  # traer + detener
```

Procedimiento completo de arranque: [`docs/arranque-gpu-vast.md`](../../docs/arranque-gpu-vast.md).

Protecciones

- **Código inmutable**: cada commit se sube a una carpeta nueva; nunca se sobrescribe código ni datos remotos (`rsync --ignore-existing`).
- **Preflight**: GPU sin procesos, `/workspace/ora.lock` libre, disco ≥ `DISCO_MIN_GB`, Blender 5.2.3 y escenas protegidas
  (`PROTEGIDAS`) con el mismo SHA-256 que en la primera comprobación.
- **Bloqueo**: `ejecutar` crea `/workspace/ora.lock` con agente, script y hora; lo libera aunque Blender falle. Registra
  `blender.log`, `gpu.csv` (uso, VRAM, potencia cada segundo) y `resumen.txt` en `paquete/_registros/`.
- **`ejecutar` sin `--confirmar` no ejecuta**: imprime el comando (los renders requieren aprobación del usuario).
- **`traer`** rechaza rutas absolutas o con `..`, copia sin sobrescribir a `~/Downloads/ora-vast-respaldo/<fecha>/` y verifica
  todo contra un manifiesto SHA-256 generado en la instancia.
- **`detener`** solo actúa si el último `traer` se verificó; detiene (no destruye), comprueba que la instancia dejó de
  responder y anota duración y costo en `docs/registro-gpu.md`.

Prueba sin instancia (simulación local, sin tocar Vast):

```bash
ORA_VAST_LOCAL=1 ORA_VAST_RAIZ_LOCAL=/ruta/simulada/workspace VAST_ENV=/dev/null VAST_BLENDER=/workspace/fakeblender \
RESPALDO_MAC=/tmp/resp ORA_ESTADO=/tmp/estado ORA_REGISTRO=/tmp/registro.md tools/vast/sesion.sh preflight
```

`tools/vast/vast.env` y `tools/vast/.estado/` están ignorados por Git (datos de la sesión local).
