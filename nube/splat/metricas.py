"""Prueba objetiva «¿el splat supera a la V5?» en las vistas de control (nunca entrenadas).

    python metricas.py <datos> <ckpt.pt> <salida> [<carpeta_referencia_v5>]

Para cada vista de control: referencia = render de Cycles (datos/control/<id>.png); candidato 1 = el splat renderizado
con gsplat desde la misma pose; candidato 2 = la captura de la V5 en el navegador desde la misma pose
(referencia_v5/<id>.png, 1280×720, tomada en el Mac con apartamento-102/tools/capturar_control.mjs).
Métricas frente a Cycles: PSNR (↑), SSIM (↑) y LPIPS-VGG (↓, la más cercana a la percepción humana).
Salida: metricas.json, splat_control/<id>.png y hojas comparativas <id>_cycles-v5-splat.jpg.
"""
import json, math, os, sys
import numpy as np, torch
from PIL import Image, ImageDraw
from gsplat.rendering import rasterization
from torchmetrics.image import PeakSignalNoiseRatio, StructuralSimilarityIndexMeasure
from torchmetrics.image.lpip import LearnedPerceptualImagePatchSimilarity

datos, ckpt, salida = sys.argv[1:4]; ref_v5 = sys.argv[4] if len(sys.argv) > 4 else None
os.makedirs(os.path.join(salida, 'splat_control'), exist_ok=True)
dev = 'cuda'
ctl = json.load(open(os.path.join(datos, 'control.json')))
W, H = ctl['w'], ctl['h']; f = 0.5 * W / math.tan(0.5 * ctl['camera_angle_x'])
K = torch.tensor([[f, 0, W / 2], [0, f, H / 2], [0, 0, 1]], dtype=torch.float32, device=dev)[None]
sp = torch.load(ckpt, map_location=dev, weights_only=True)['splats']
n_gauss = sp['means'].shape[0]
colors = torch.cat([sp['sh0'], sp['shN']], 1); grado = int(math.sqrt(colors.shape[1])) - 1
psnr = PeakSignalNoiseRatio(data_range=1.0).to(dev); ssim = StructuralSimilarityIndexMeasure(data_range=1.0).to(dev)
lpips = LearnedPerceptualImagePatchSimilarity(net_type='vgg', normalize=True).to(dev)


def cargar(ruta):
    im = Image.open(ruta).convert('RGB')
    if im.size != (W, H): im = im.resize((W, H), Image.LANCZOS)
    return torch.from_numpy(np.asarray(im, np.float32) / 255).permute(2, 0, 1)[None].to(dev)


def medir(a, b):
    return {'psnr': round(float(psnr(a, b)), 3), 'ssim': round(float(ssim(a, b)), 4), 'lpips': round(float(lpips(a, b)), 4)}


filas = []
for fr in ctl['frames']:
    c2w = np.array(fr['transform_matrix'], np.float64) @ np.diag([1, -1, -1, 1])   # OpenGL → OpenCV (igual que a_colmap)
    vm = torch.tensor(np.linalg.inv(c2w), dtype=torch.float32, device=dev)[None]
    with torch.no_grad():
        img, _, _ = rasterization(sp['means'], sp['quats'], torch.exp(sp['scales']), torch.sigmoid(sp['opacities']), colors,
                                  vm, K, W, H, sh_degree=grado)
    img = img[0].clamp(0, 1).permute(2, 0, 1)[None]
    Image.fromarray((img[0].permute(1, 2, 0).cpu().numpy() * 255).round().astype(np.uint8)).save(os.path.join(salida, 'splat_control', f"{fr['id']}.png"))
    ref = cargar(os.path.join(datos, fr['file_path']))
    fila = {'id': fr['id'], 'splat': medir(img, ref)}
    v5 = os.path.join(ref_v5, f"{fr['id']}.png") if ref_v5 else None
    if v5 and os.path.exists(v5): fila['v5'] = medir(cargar(v5), ref)
    filas.append(fila)
    # hoja: Cycles | V5 | splat
    paneles = [Image.open(os.path.join(datos, fr['file_path'])).convert('RGB').resize((W // 2, H // 2))]
    if 'v5' in fila: paneles.append(Image.open(v5).convert('RGB').resize((W // 2, H // 2)))
    paneles.append(Image.open(os.path.join(salida, 'splat_control', f"{fr['id']}.png")).resize((W // 2, H // 2)))
    hoja = Image.new('RGB', (W // 2 * len(paneles), H // 2)); d = ImageDraw.Draw(hoja)
    for i, (p, t) in enumerate(zip(paneles, ['Cycles (referencia)'] + (['V5'] if 'v5' in fila else []) + ['Splat'])):
        hoja.paste(p, (i * W // 2, 0)); d.rectangle([i * W // 2, 0, i * W // 2 + 170, 22], fill=(0, 0, 0)); d.text((i * W // 2 + 6, 5), t, fill=(255, 255, 255))
    hoja.save(os.path.join(salida, f"{fr['id']}_cycles-v5-splat.jpg"), quality=90)
    print(json.dumps(fila), flush=True)


def media(clave, m):
    v = [r[clave][m] for r in filas if clave in r]; return round(sum(v) / len(v), 4) if v else None


resumen = {k: {m: media(k, m) for m in ('psnr', 'ssim', 'lpips')} for k in ('splat', 'v5')}
gana = None
if resumen['v5']['lpips'] is not None:
    gana = {'lpips_mejor_en_%': round(100 * (resumen['v5']['lpips'] - resumen['splat']['lpips']) / resumen['v5']['lpips'], 1),
            'vistas_donde_splat_gana_lpips': sum(1 for r in filas if 'v5' in r and r['splat']['lpips'] < r['v5']['lpips']), 'vistas': len(filas)}
json.dump({'gaussianas': n_gauss, 'grado_sh': grado, 'por_vista': filas, 'media': resumen, 'comparacion': gana},
          open(os.path.join(salida, 'metricas.json'), 'w'), indent=1)
print(json.dumps({'gaussianas': n_gauss, 'media': resumen, 'comparacion': gana}, indent=1))
