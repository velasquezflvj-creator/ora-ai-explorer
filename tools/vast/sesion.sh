#!/bin/bash
# ORA AI Explorer · sesión de GPU en Vast.ai, de principio a fin y con protecciones.
# Apartamento 102: propuesta de redistribución conceptual (no planta verificada).
#
#   tools/vast/sesion.sh <orden> [opciones]
#
# Órdenes
#   estado                       Conexión, GPU, bloqueo, disco, Blender y costo por hora de la instancia.
#   subir                        Copia blender/produccion/ del commit actual a paquete/_codigo/<rama>-<commit>/ (carpeta
#                                nueva e inmutable; nunca sobrescribe código ni datos remotos).
#   preflight                    GPU sin procesos, bloqueo libre, disco libre, Blender 5.2.3 y escenas protegidas intactas.
#   ejecutar --agente A --escena E --script S [--confirmar] -- ARGS
#                                Toma /workspace/ora.lock, ejecuta Blender en segundo plano registrando el uso de GPU y libera
#                                el bloqueo. Sin --confirmar solo muestra lo que haría (las tareas de render requieren aprobación).
#   traer RUTA [RUTA…]           Trae rutas relativas al paquete al respaldo del Mac (sin sobrescribir) y verifica SHA-256.
#   detener                      Solo si el último «traer» se verificó: detiene (NO destruye) la instancia y comprueba que
#                                dejó de responder; anota tiempo y costo en docs/registro-gpu.md.
#   cerrar RUTA [RUTA…]          traer + detener.
#
# Opciones globales: --seco (muestra comandos sin ejecutarlos) · VAST_ENV=archivo (configuración; por defecto tools/vast/vast.env)
# Modo de prueba: ORA_VAST_LOCAL=1 ejecuta los comandos «remotos» en este Mac sobre ORA_VAST_RAIZ_LOCAL (simulación).
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
CONF="${VAST_ENV:-$REPO/tools/vast/vast.env}"
[[ -f "$CONF" ]] && source "$CONF"
: "${VAST_HOST:=}" "${VAST_PUERTO:=}" "${VAST_LLAVE:=$HOME/.ssh/vast_59585596}" "${VAST_USUARIO:=root}"
: "${VAST_PAQUETE:=/workspace/ora_restore_4080/proyecto_ora/paquete}"
: "${VAST_BLENDER:=/workspace/blender-5.2.3-linux-x64/blender}"
: "${RESPALDO_MAC:=$HOME/Downloads/ora-vast-respaldo}"
: "${PROTEGIDAS:=escena/escena_splat.blend escena/escena_splat_v2.blend v4/escena_v4.blend v4/escena_v4_1.blend}"
: "${DISCO_MIN_GB:=5}"
LOCAL="${ORA_VAST_LOCAL:-0}"; SECO=0
ESTADO_DIR="${ORA_ESTADO:-$REPO/tools/vast/.estado}"; mkdir -p "$ESTADO_DIR"
REGISTRO="${ORA_REGISTRO:-$REPO/docs/registro-gpu.md}"

msg() { printf '[vast] %s\n' "$*"; }
falla() { printf '[vast] ERROR: %s\n' "$*" >&2; exit 1; }
ssh_opts() { echo "-i $VAST_LLAVE -p $VAST_PUERTO -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=15 -o LogLevel=ERROR"; }

# Ejecuta un comando en la instancia (o localmente en modo simulación, con /workspace → ORA_VAST_RAIZ_LOCAL)
remoto() {
  local cmd="$1"
  if [[ "$LOCAL" == 1 ]]; then cmd="${cmd//\/workspace/$ORA_VAST_RAIZ_LOCAL}"; cmd="${cmd//sha256sum/shasum -a 256}"; fi
  if [[ "$SECO" == 1 ]]; then msg "(seco) remoto: $cmd"; return 0; fi
  if [[ "$LOCAL" == 1 ]]; then bash -c "$cmd"; else
    [[ -n "$VAST_HOST" && -n "$VAST_PUERTO" ]] || falla "falta VAST_HOST/VAST_PUERTO en $CONF"
    ssh $(ssh_opts) "$VAST_USUARIO@$VAST_HOST" "$cmd" 2> >(grep -v -e '^AI agents: READ' -e '^Welcome to vast' -e '^Have fun' -e 'If authentication' >&2)
  fi
}
ruta_remota() { if [[ "$LOCAL" == 1 ]]; then echo "${1//\/workspace/$ORA_VAST_RAIZ_LOCAL}"; else echo "$VAST_USUARIO@$VAST_HOST:$1"; fi; }
sincronizar() {   # rsync origen destino (sin sobrescribir nunca)
  local o="$1" d="$2"
  if [[ "$SECO" == 1 ]]; then msg "(seco) rsync --ignore-existing $o $d"; return 0; fi
  if [[ "$LOCAL" == 1 ]]; then rsync -a --ignore-existing "$o" "$d"; else rsync -a --ignore-existing -e "ssh $(ssh_opts)" "$o" "$d"; fi
}

cmd_estado() {
  remoto "echo \"instancia: \${CONTAINER_ID:-local}\"; nvidia-smi --query-gpu=name,utilization.gpu,memory.used --format=csv,noheader 2>/dev/null || echo 'GPU: no disponible';
    nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader 2>/dev/null | sed 's/^/proceso GPU: /';
    if [ -d /workspace/ora.lock ]; then echo \"bloqueo: OCUPADO → \$(cat /workspace/ora.lock/info 2>/dev/null)\"; else echo 'bloqueo: libre'; fi;
    df -h /workspace | tail -1 | awk '{print \"disco libre: \" \$4}';
    $VAST_BLENDER --version 2>/dev/null | head -1 || echo 'Blender: no encontrado';
    if command -v vastai >/dev/null && [ -n \"\${CONTAINER_API_KEY:-}\" ]; then vastai show instance \$CONTAINER_ID --api-key \"\$CONTAINER_API_KEY\" --raw 2>/dev/null | jq -r '\"costo: \(.dph_total) USD/h (almacenamiento \(.storage_total_cost) USD/h) · estado \(.actual_status)\"'; fi"
}

cmd_subir() {
  local rama commit dest
  rama="$(git -C "$REPO" rev-parse --abbrev-ref HEAD | tr '/' '_')"; commit="$(git -C "$REPO" rev-parse --short HEAD)"
  git -C "$REPO" diff --quiet -- blender/produccion || falla "blender/produccion tiene cambios sin commit: suba solo código versionado"
  dest="$VAST_PAQUETE/_codigo/$rama-$commit"
  remoto "test ! -e '$dest' || { echo 'ya existe $dest (inmutable): no se sobrescribe'; exit 3; }; mkdir -p '$dest'"
  local tmp; tmp="$(mktemp -d)"; git -C "$REPO" archive HEAD blender/produccion | tar -x -C "$tmp"
  sincronizar "$tmp/blender/produccion/" "$(ruta_remota "$dest/")"; rm -rf "$tmp"
  echo "$dest" > "$ESTADO_DIR/codigo_remoto"; msg "código del commit $commit en $dest"
}

cmd_preflight() {
  local lista="" e; for e in $PROTEGIDAS; do lista="$lista $e"; done
  [[ -f "$ESTADO_DIR/protegidas.sha256" ]] || {
    msg "registrando hashes de referencia de las escenas protegidas (primera vez)"
    remoto "cd $VAST_PAQUETE && sha256sum $lista" > "$ESTADO_DIR/protegidas.sha256"; }
  local ref; ref="$(cat "$ESTADO_DIR/protegidas.sha256")"
  remoto "set -e; cd $VAST_PAQUETE
    n=\$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -c . || true); [ \"\$n\" = 0 ] || { echo 'GPU ocupada por otro proceso'; exit 10; }
    [ ! -d /workspace/ora.lock ] || { echo \"bloqueo ocupado: \$(cat /workspace/ora.lock/info)\"; exit 11; }
    libre=\$(df -BG --output=avail /workspace 2>/dev/null | tail -1 | tr -dc 0-9); [ -z \"\$libre\" ] || [ \"\$libre\" -ge $DISCO_MIN_GB ] || { echo \"disco libre \${libre} GB < $DISCO_MIN_GB\"; exit 12; }
    [ ! -x $VAST_BLENDER ] || $VAST_BLENDER --version | head -1 | grep -q '5.2.3' || { echo 'Blender no es 5.2.3'; exit 13; }
    printf '%s\n' \"$ref\" | sha256sum -c --quiet || { echo 'una escena protegida cambió'; exit 14; }
    echo 'preflight correcto'"
}

cmd_ejecutar() {
  local agente="" escena="" script="" confirmar=0
  while [[ $# -gt 0 && "$1" != "--" ]]; do case "$1" in
    --agente) agente="$2"; shift 2;; --escena) escena="$2"; shift 2;; --script) script="$2"; shift 2;; --confirmar) confirmar=1; shift;;
    *) falla "opción desconocida: $1";; esac; done
  [[ "${1:-}" == "--" ]] && shift
  [[ -n "$agente" && -n "$escena" && -n "$script" ]] || falla "uso: ejecutar --agente A --escena E --script S [--confirmar] -- ARGS"
  local codigo; codigo="$(cat "$ESTADO_DIR/codigo_remoto" 2>/dev/null)" || falla "primero: subir"
  [[ "$script" == /* ]] || script="$codigo/$script"
  local marca; marca="$(date -u +%Y%m%dT%H%M%SZ)"; local log="$VAST_PAQUETE/_registros/$marca-$(basename "$script" .py)"
  local cmd="$VAST_BLENDER -b '$escena' --python '$script' -- $*"
  if [[ "$confirmar" != 1 ]]; then msg "PLAN (sin --confirmar no se ejecuta): cd $VAST_PAQUETE && $cmd"; return 0; fi
  cmd_preflight
  remoto "set -e; cd $VAST_PAQUETE; mkdir /workspace/ora.lock || { echo 'bloqueo ocupado'; exit 11; }
    trap 'rm -rf /workspace/ora.lock' EXIT
    echo \"$agente · \$(basename '$script') · inicio $marca\" > /workspace/ora.lock/info; mkdir -p '$log'
    (nvidia-smi --query-gpu=timestamp,utilization.gpu,memory.used,power.draw --format=csv,noheader,nounits -lms 1000 > '$log/gpu.csv' 2>/dev/null &
     echo \$! > '$log/gpu.pid')
    t0=\$(date +%s); set +e; $cmd > '$log/blender.log' 2>&1; rc=\$?; set -e
    kill \$(cat '$log/gpu.pid') 2>/dev/null || true; echo \"rc=\$rc segundos=\$((\$(date +%s)-t0)) agente=$agente\" > '$log/resumen.txt'
    cat '$log/resumen.txt'; exit \$rc"
  echo "$log" > "$ESTADO_DIR/ultimo_registro"
}

cmd_traer() {
  [[ $# -gt 0 ]] || falla "uso: traer RUTA [RUTA…] (relativas al paquete)"
  local marca dest m="$ESTADO_DIR/traido.sha256"; marca="$(date -u +%Y%m%dT%H%M%SZ)"
  local r rel=""; for r in "$@"; do [[ "$r" != /* && "$r" != *..* ]] || falla "ruta no permitida: $r"; rel="$rel '$r'"; done
  dest="$RESPALDO_MAC/$marca"; [[ "$SECO" == 1 ]] || mkdir -p "$dest"
  rm -f "$ESTADO_DIR/verificado"   # un nuevo «traer» invalida la verificación anterior hasta completarse
  remoto "cd $VAST_PAQUETE && find $rel -type f -print0 | sort -z | xargs -0 sha256sum" > "$m" || falla "no se pudo generar el manifiesto remoto"
  for r in "$@"; do [[ "$SECO" == 1 ]] || mkdir -p "$dest/$(dirname "$r")"; sincronizar "$(ruta_remota "$VAST_PAQUETE/$r")" "$dest/$(dirname "$r")/"; done
  [[ "$SECO" == 1 ]] && return 0
  cp "$m" "$dest/MANIFIESTO.sha256"
  ( cd "$dest" && shasum -a 256 -c --quiet MANIFIESTO.sha256 ) || falla "verificación SHA-256 FALLIDA en $dest: no se detiene la instancia"
  echo "$dest" > "$ESTADO_DIR/verificado"; msg "traído y verificado: $(wc -l < "$m" | tr -d ' ') archivos en $dest"
}

cmd_detener() {
  [[ -s "$ESTADO_DIR/verificado" ]] || falla "no hay respaldo verificado de esta sesión: ejecute «traer» antes de detener"
  local info; info="$(remoto 'vastai show instance $CONTAINER_ID --api-key "$CONTAINER_API_KEY" --raw 2>/dev/null | jq -r "[.id, .dph_total, .storage_total_cost, .duration] | @tsv"' || true)"
  msg "deteniendo (no destruyendo) la instancia…"
  remoto 'vastai stop instance $CONTAINER_ID --api-key "$CONTAINER_API_KEY"' || true
  if [[ "$SECO" == 1 || "$LOCAL" == 1 ]]; then msg "(simulación) comprobación de parada omitida"; else
    local i; for i in 1 2 3 4 5 6; do sleep 10
      if ! ssh $(ssh_opts) -o ConnectTimeout=8 "$VAST_USUARIO@$VAST_HOST" true 2>/dev/null; then msg "instancia detenida: no responde por SSH"; break; fi
      [[ $i == 6 ]] && falla "la instancia sigue respondiendo tras 60 s: revise la consola de Vast"; done
  fi
  registrar "$info"
}

registrar() {
  local id dph alm dur; IFS=$'\t' read -r id dph alm dur <<< "${1:-}"
  [[ -f "$REGISTRO" ]] || printf '# Registro de sesiones de GPU (Vast.ai)\n\n| Fecha (UTC) | Instancia | Duración | USD/h total | USD/h almacenamiento | Costo estimado | Respaldo |\n|---|---|---|---|---|---|---|\n' > "$REGISTRO"
  local horas costo; horas="$(awk -v s="${dur:-0}" 'BEGIN{printf "%.2f", s/3600}')"; costo="$(awk -v s="${dur:-0}" -v d="${dph:-0}" 'BEGIN{printf "%.2f", s/3600*d}')"
  printf '| %s | %s | %s h | %s | %s | %s USD | %s |\n' "$(date -u '+%Y-%m-%d %H:%M')" "${id:--}" "$horas" "${dph:--}" "${alm:--}" "$costo" "$(cat "$ESTADO_DIR/verificado" 2>/dev/null)" >> "$REGISTRO"
  msg "anotado en ${REGISTRO#$REPO/}"
}

[[ "${1:-}" == "--seco" ]] && { SECO=1; shift; }
orden="${1:-ayuda}"; shift || true
case "$orden" in
  estado) cmd_estado;; subir) cmd_subir;; preflight) cmd_preflight;; ejecutar) cmd_ejecutar "$@";;
  traer) cmd_traer "$@";; detener) cmd_detener;; cerrar) cmd_traer "$@"; cmd_detener;;
  ayuda|-h|--help) sed -n '2,24p' "$0" | sed 's/^# \{0,1\}//';;
  *) falla "orden desconocida: $orden (use: ayuda)";;
esac
