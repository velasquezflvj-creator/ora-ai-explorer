#!/bin/zsh
# Prepara en el Mac el paquete que se sube a la GPU en la nube para el piloto de Gaussian Splatting.
# No modifica los archivos maestros: Blender abre el .blend V3 en segundo plano y guarda una COPIA dentro del paquete;
# los hashes de los maestros se comparan antes y después y el script falla si alguno cambió.
#
#   zsh tools/splat/preparar_paquete.sh [carpeta_salida]      (por defecto: ../ora-splat-paquete, fuera del repositorio)
#
# Resultado: <salida>/ora-splat-paquete.tar.gz + MANIFIESTO.sha256 (verificable en la nube con «shasum -c»).
set -euo pipefail
RAIZ=${0:A:h:h:h}
SALIDA=${1:-${RAIZ:h}/ora-splat-paquete}
BLENDER=${BLENDER:-/Volumes/Blender/Blender.app/Contents/MacOS/Blender}
[[ -x $BLENDER ]] || BLENDER=/Applications/Blender.app/Contents/MacOS/Blender
cd $RAIZ
MAESTROS=(blender/Apartamento_102_Render_Master.blend blender/Apartamento_102_Render_V3.blend blender/Apartamento_102_Video.blend apartamento-102/modelo/apto-102-propuesta.glb)
antes=$(shasum -a 256 $MAESTROS)

# memoria y disco antes de abrir Blender (8 GB de RAM: no se lanza si hay menos de ~1,5 GB recuperables)
libre_mb=$(vm_stat | awk '/page size/{ps=$8} /Pages free/{f=$3} /Pages inactive/{i=$3} /Pages speculative/{s=$3} END{print int((f+i+s)*ps/1048576)}')
disco_gb=$(df -g . | awk 'NR==2{print $4}')
echo "[paquete] memoria recuperable ≈ ${libre_mb} MB · disco libre ${disco_gb} GB"
(( libre_mb > 1500 )) || { echo "[paquete] memoria insuficiente: cierre aplicaciones y repita"; exit 1; }
(( disco_gb > 5 )) || { echo "[paquete] disco insuficiente"; exit 1; }

rm -rf $SALIDA/paquete; mkdir -p $SALIDA/paquete
P=$SALIDA/paquete
$BLENDER -b blender/Apartamento_102_Render_V3.blend --python blender/scripts/empaquetar_splat.py -- \
  blender/scripts/apto-102.json $P 2>&1 | grep -E '^\[paquete\]|Error|error' || true
[[ -f $P/escena/escena_splat.blend ]] || { echo "[paquete] ERROR: no se generó la copia"; exit 1; }

despues=$(shasum -a 256 $MAESTROS)
[[ $antes == $despues ]] || { echo "[paquete] ERROR: un archivo maestro cambió"; diff <(echo $antes) <(echo $despues); exit 1; }
echo "[paquete] maestros intactos (SHA-256 iguales antes y después)"

mkdir -p $P/blender/scripts $P/apartamento-102/data $P/nube $P/datos
cp blender/scripts/{camaras_splat.py,apto-102.json,piloto_v5.py} $P/blender/scripts/
cp apartamento-102/data/propuesta-102.json $P/apartamento-102/data/
cp -R nube/splat $P/nube/ && rm -rf $P/nube/splat/__pycache__
[[ -d $SALIDA/referencia_v5 ]] && cp -R $SALIDA/referencia_v5 $P/referencia_v5
echo "$antes" > $P/maestros.sha256   # constancia de los hashes de los maestros en el momento de empaquetar
(cd $P && find . -type f ! -name MANIFIESTO.sha256 | sort | xargs shasum -a 256 > MANIFIESTO.sha256)
tar -C $SALIDA -czf $SALIDA/ora-splat-paquete.tar.gz paquete
shasum -a 256 $SALIDA/ora-splat-paquete.tar.gz | tee $SALIDA/ora-splat-paquete.tar.gz.sha256
du -sh $SALIDA/ora-splat-paquete.tar.gz
