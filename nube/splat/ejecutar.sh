#!/bin/bash
# Piloto de Gaussian Splatting en la GPU de la nube, de principio a fin, con topes de costo.
#   cd /workspace/paquete && TARIFA_USD_H=0.34 bash nube/splat/ejecutar.sh [etapa_inicial]
# Etapas (reanudable: cada una deja un archivo registro/OK_<etapa>; se puede empezar en cualquiera):
#   verificar  hashes del paquete (MANIFIESTO.sha256) + guardián de costos en segundo plano
#   instalar   Blender 5.2.3, torch 2.4.1+cu124, gsplat 1.5.3 (nube/splat/instalar.sh)
#   humo       prueba de humo barata: 4 vistas a 32 muestras + 300 pasos + métricas (≈ 5 min); si falla, se detiene todo
#   render     556 vistas + 10 de control con Cycles/OptiX (MUESTRAS, por defecto 128); tras 12 vistas proyecta el
#              tiempo total y ABORTA si el render no cabe en el presupuesto
#   colmap     poses exactas → sparse/0 (binario)
#   entrenar   30 000 pasos de gsplat (PASOS)
#   metricas   splat vs V5 vs Cycles en las vistas de control
#   empacar    resultados/ora-splat-resultados.tar.gz y registro/LISTO (el guardián detiene la máquina tras la gracia)
set -euo pipefail
cd "$(dirname "$0")/../.."; P=$PWD
REG=$P/registro; mkdir -p $REG; exec > >(tee -a $REG/ejecutar.log) 2>&1
LIMITE_H=${LIMITE_H:-4}; MUESTRAS=${MUESTRAS:-128}; PASOS=${PASOS:-30000}; TARIFA=${TARIFA_USD_H:?Indique TARIFA_USD_H (precio por hora de la máquina)}
PRESUPUESTO=${PRESUPUESTO_USD:-15}
ETAPAS=(verificar instalar humo render colmap entrenar metricas empacar)
INICIO=${1:-verificar}
BL="blender -b escena/escena_splat.blend --python blender/scripts/camaras_splat.py -- blender/scripts/apto-102.json"
REF_V5=$P/referencia_v5; [[ -d $REF_V5 ]] || REF_V5=""
t0=$(date +%s)
costo() { python3 -c "print(round(($(date +%s)-$t0)/3600*$TARIFA,2))"; }
etapa() { echo "$1" > $REG/ETAPA; echo "== $(date -u +%T) etapa $1 · costo de esta sesión ≈ $(costo) USD"; }
ok() { touch $REG/OK_$1; : > $REG/ETAPA; }
activo=0
for e in "${ETAPAS[@]}"; do
  [[ $e == $INICIO ]] && activo=1
  (( activo )) || continue
  [[ -f $REG/OK_$e ]] && { echo "== etapa $e ya hecha"; continue; }
  case $e in
  verificar)
    etapa verificar
    sha256sum -c --quiet MANIFIESTO.sha256 && echo "paquete íntegro (SHA-256)"
    pgrep -f guardian.sh >/dev/null || TARIFA_USD_H=$TARIFA nohup bash nube/splat/guardian.sh $LIMITE_H >/dev/null 2>&1 &
    python3 -c "
import sys; h=$LIMITE_H; t=$TARIFA; p=$PRESUPUESTO
print(f'tope del guardián: {h} h × {t} USD/h = {h*t:.2f} USD (presupuesto {p} USD)')
sys.exit(0 if h*t <= p else 1)" || { echo "ERROR: LIMITE_H × TARIFA supera el presupuesto"; exit 1; }
    ok verificar ;;
  instalar)
    etapa instalar; bash nube/splat/instalar.sh; ok instalar ;;
  humo)
    etapa humo; H=$P/humo; rm -rf $H; mkdir -p $H
    $BL $H --renderizar --control --dispositivo OPTIX --muestras 32 --desde 0 --hasta 4 2>&1 | grep -E '^\[splat\]|Error' || true
    (( $(ls $H/images | wc -l) == 4 )) || { echo "ERROR humo: render"; exit 1; }
    source /workspace/ora/venv/bin/activate
    python nube/splat/a_colmap.py $H escena/puntos_iniciales.txt
    python nube/splat/entrenar.py $H $H/res --prueba 2>&1 | tail -5
    python nube/splat/metricas.py $H "$(ls $H/res/ckpts/*.pt | tail -1)" $H/met $REF_V5 | tail -12
    ls $H/res/ply/*.ply >/dev/null && echo "prueba de humo correcta" ; ok humo ;;
  render)
    etapa render; D=$P/datos
    $BL $D --planificar 2>&1 | grep -E '^\[splat\]'
    $BL $D --renderizar --dispositivo OPTIX --muestras $MUESTRAS --desde 0 --hasta 12 2>&1 | grep -E '^\[splat\]|Error' || true
    python3 - <<PY || { echo "ABORTADO: el render completo no cabe en el presupuesto"; exit 1; }
import csv; f=[float(r[3]) for r in csv.reader(open('$D/render_log.csv'))]; s=sum(f)/len(f)
h=(566*s)/3600; usd=h*$TARIFA
print(f'render: {s:.1f} s/vista → proyección {566*s/60:.0f} min ≈ {usd:.2f} USD')
import sys; sys.exit(0 if h < $LIMITE_H*0.5 else 1)
PY
    $BL $D --renderizar --control --dispositivo OPTIX --muestras $MUESTRAS 2>&1 | grep -E '^\[splat\]|Error' | tail -3 || true
    n=$(ls $D/images | wc -l); echo "vistas renderizadas: $n"; (( n >= 550 )) || { echo "ERROR: faltan vistas"; exit 1; }
    ok render ;;
  colmap)
    etapa colmap; source /workspace/ora/venv/bin/activate; python nube/splat/a_colmap.py $P/datos escena/puntos_iniciales.txt; ok colmap ;;
  entrenar)
    etapa entrenar; source /workspace/ora/venv/bin/activate
    python nube/splat/entrenar.py $P/datos $P/resultados/entreno --pasos $PASOS --max-gaussianas ${MAX_GAUSS:-1000000} 2>&1 | grep -vE '^\s*[0-9]+%|it/s' | tail -40
    ok entrenar ;;
  metricas)
    etapa metricas; source /workspace/ora/venv/bin/activate
    python nube/splat/metricas.py $P/datos "$(ls $P/resultados/entreno/ckpts/ckpt_*_rank0.pt | sort -V | tail -1)" $P/resultados/metricas $REF_V5
    ok metricas ;;
  empacar)
    etapa empacar; R=$P/resultados
    cp "$(ls $R/entreno/ply/*.ply | sort -V | tail -1)" $R/splat_sala_cocina.ply
    cp -R $P/datos/control $R/cycles_control; cp $P/datos/{transforms.json,control.json,render_log.csv} $R/
    cp -R $REG $R/registro; nvidia-smi > $R/registro/gpu.txt
    tar -C $P -czf $R/ora-splat-resultados.tar.gz resultados/splat_sala_cocina.ply resultados/metricas resultados/cycles_control \
      resultados/transforms.json resultados/control.json resultados/render_log.csv resultados/registro resultados/entreno/stats 2>/dev/null || true
    sha256sum $R/ora-splat-resultados.tar.gz | tee $R/ora-splat-resultados.tar.gz.sha256; du -sh $R/ora-splat-resultados.tar.gz
    ok empacar; touch $REG/LISTO
    echo "== LISTO · costo de esta sesión ≈ $(costo) USD · la máquina se detendrá en ${GRACIA_MIN:-45} min (descargue los resultados ya)" ;;
  esac
done
