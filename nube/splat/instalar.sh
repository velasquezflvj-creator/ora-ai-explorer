#!/bin/bash
# Instala en la máquina de la nube (Ubuntu 22.04 + GPU NVIDIA, imagen CUDA 12.4 «devel») todo lo del piloto:
#   Blender 5.2.3 LTS (la misma versión del Mac; SHA-256 oficial verificado), Python 3.10 en un entorno propio,
#   torch 2.4.1+cu124, gsplat 1.5.3 (rueda precompilada oficial) y su entrenador de ejemplo (etiqueta v1.5.3).
# Versiones fijas: las ruedas de gsplat 1.5.3 solo existen para Python 3.10 / torch 2.4 / CUDA 12.4.
# Uso:  bash nube/splat/instalar.sh            (desde la carpeta «paquete»; ≈ 8–12 min; ≈ 12 GB de disco)
set -euo pipefail
cd "$(dirname "$0")/../.."
BASE=/workspace/ora; mkdir -p $BASE; LOG=$PWD/registro; mkdir -p $LOG
exec > >(tee -a $LOG/instalar.log) 2>&1
echo "== $(date -u +%FT%TZ) instalación"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
NV=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1 | cut -d. -f1)
(( NV >= 550 )) || { echo "ERROR: controlador NVIDIA $NV < 550 (CUDA 12.4). Elija otra máquina."; exit 1; }
df -h /workspace | tail -1

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3.10 python3.10-venv python3.10-dev git curl xz-utils ca-certificates \
  libxrender1 libxxf86vm1 libxfixes3 libxi6 libxkbcommon0 libsm6 libice6 libgl1 libegl1 libglib2.0-0 libx11-6 >/dev/null

# --- Blender 5.2.3 (verificado contra el SHA-256 publicado por blender.org)
BL=blender-5.2.3-linux-x64
if [[ ! -x $BASE/$BL/blender ]]; then
  curl -fsSL -o $BASE/$BL.tar.xz https://download.blender.org/release/Blender5.2/$BL.tar.xz
  echo "78486c018b4443efe5e75ab54c290ed8c15abafd249b862c2c9ce2530a918eec  $BASE/$BL.tar.xz" | sha256sum -c -
  tar -C $BASE -xf $BASE/$BL.tar.xz && rm $BASE/$BL.tar.xz
fi
ln -sf $BASE/$BL/blender /usr/local/bin/blender
blender -b --factory-startup --python-expr "import bpy,sys;cp=bpy.context.preferences.addons['cycles'].preferences;cp.compute_device_type='OPTIX';cp.refresh_devices();print('OPTIX', [d.name for d in cp.devices if d.type=='OPTIX'])" 2>&1 | grep -E '^OPTIX|Blender 5'

# --- entorno de entrenamiento
if [[ ! -x $BASE/venv/bin/python ]]; then python3.10 -m venv $BASE/venv; fi
source $BASE/venv/bin/activate
pip install -q --upgrade pip wheel setuptools ninja
pip install -q torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cu124
pip install -q gsplat==1.5.3 --index-url https://docs.gsplat.studio/whl/pt24cu124 --extra-index-url https://pypi.org/simple
[[ -d $BASE/gsplat ]] || git clone -q --depth 1 --branch v1.5.3 https://github.com/nerfstudio-project/gsplat.git $BASE/gsplat
pip install -q "numpy<2.0.0"
TORCH_CUDA_ARCH_LIST="8.9" pip install -q --no-build-isolation -r $BASE/gsplat/examples/requirements.txt   # 8.9 = RTX 4090 / L40S / L4
python - <<'PY'
import torch, gsplat
print('torch', torch.__version__, 'cuda', torch.version.cuda, 'gpu', torch.cuda.get_device_name(0), 'gsplat', gsplat.__version__)
import fused_ssim, pycolmap  # noqa: F401  (dependencias del entrenador de ejemplo)
# prueba mínima del rasterizador en la GPU
from gsplat import rasterization
d = 'cuda'; N = 1000
img, a, _ = rasterization(torch.randn(N, 3, device=d) + torch.tensor([0, 0, 4.0], device=d), torch.nn.functional.normalize(torch.randn(N, 4, device=d), dim=-1),
    torch.full((N, 3), 0.02, device=d), torch.full((N,), 0.8, device=d), torch.rand(N, 3, device=d),
    torch.eye(4, device=d)[None], torch.tensor([[[300., 0, 160], [0, 300., 120], [0, 0, 1]]], device=d), 320, 240)
print('rasterizacion_ok', tuple(img.shape), float(a.mean()) > 0)
PY
echo "== instalación completa $(date -u +%FT%TZ)"
