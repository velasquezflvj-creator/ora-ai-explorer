#!/bin/bash
# Guardián de costos: detiene la máquina de la nube aunque nadie esté mirando.
#   bash nube/splat/guardian.sh <horas_límite> &      (lo lanza ejecutar.sh al empezar)
# Detiene la instancia (RunPod o Vast.ai, detectados por sus variables de entorno) cuando ocurre lo primero de:
#   1. se cumple el límite de horas desde el arranque del guardián (tope duro del presupuesto);
#   2. existe el archivo registro/LISTO y pasaron GRACIA_MIN minutos (tiempo para descargar los resultados);
#   3. la GPU lleva INACTIVA_MIN minutos sin uso y no hay ninguna etapa en marcha (registro/ETAPA vacío).
# «Detener» apaga la GPU (deja de cobrarse); el disco sigue cobrándose (centavos/día) hasta ELIMINAR la instancia
# desde el panel o con el comando del procedimiento, después de descargar los resultados.
set -u
cd "$(dirname "$0")/../.."
LIMITE_H=${1:-4}; GRACIA_MIN=${GRACIA_MIN:-45}; INACTIVA_MIN=${INACTIVA_MIN:-20}
REG=$PWD/registro; mkdir -p $REG
inicio=$(date +%s)
fin=$(python3 -c "print(int($inicio + float('$LIMITE_H') * 3600))")
echo "$(date -u +%FT%TZ) guardián: límite $LIMITE_H h (hasta $(date -u -d @$fin +%FT%TZ)), gracia $GRACIA_MIN min, inactividad $INACTIVA_MIN min" >> $REG/guardian.log

detener() {
  echo "$(date -u +%FT%TZ) DETENER: $1" | tee -a $REG/guardian.log
  sync
  if [[ -n "${RUNPOD_POD_ID:-}" ]]; then
    runpodctl pod stop "$RUNPOD_POD_ID" 2>>$REG/guardian.log || runpodctl stop pod "$RUNPOD_POD_ID" 2>>$REG/guardian.log
  elif [[ -n "${CONTAINER_ID:-}" ]]; then
    command -v vastai >/dev/null || pip install -q vastai
    vastai stop instance "$CONTAINER_ID" --api-key "${CONTAINER_API_KEY:-}" 2>>$REG/guardian.log
  else
    echo "proveedor no detectado: apagando el sistema" >> $REG/guardian.log; shutdown -h now 2>/dev/null || poweroff
  fi
  sleep 120; echo "$(date -u +%FT%TZ) la instancia sigue viva tras la orden de detener: revisar el panel" >> $REG/guardian.log
}

inactiva=0
while true; do
  ahora=$(date +%s)
  (( ahora >= fin )) && { detener "límite de $LIMITE_H h alcanzado"; exit 0; }
  if [[ -f $REG/LISTO ]] && (( ahora - $(stat -c %Y $REG/LISTO) >= GRACIA_MIN * 60 )); then detener "trabajo terminado + $GRACIA_MIN min de gracia"; exit 0; fi
  uso=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>/dev/null | head -1 || echo 0)
  if [[ ! -s $REG/ETAPA && ! -f $REG/LISTO && ${uso:-0} -lt 5 ]]; then inactiva=$(( inactiva + 1 )); else inactiva=0; fi
  (( inactiva >= INACTIVA_MIN )) && { detener "GPU inactiva $INACTIVA_MIN min sin etapa en marcha"; exit 0; }
  printf '%s uso_gpu=%s%% transcurrido=%dmin costo_estimado=%s USD\n' "$(date -u +%T)" "${uso:-?}" $(( (ahora - inicio) / 60 )) \
    "$(python3 -c "print(round(($ahora-$inicio)/3600*float('${TARIFA_USD_H:-0}'),2))")" > $REG/estado.txt
  sleep 60
done
