"""transforms.json (cámaras de Blender, formato NeRF) → modelo COLMAP (binario), sin estimar nada: las poses son exactas.

    python a_colmap.py <datos>          # lee <datos>/transforms.json, <datos>/images y escena/puntos_iniciales.txt
                                        # escribe <datos>/sparse/0/{cameras,images,points3D}.bin

Lo leen gsplat (examples/simple_trainer.py), OpenSplat y Brush. Convenciones:
  Blender/NeRF: matriz cámara→mundo, la cámara mira a −Z con +Y arriba (OpenGL), mundo con Z arriba.
  COLMAP: mundo→cámara, la cámara mira a +Z con +Y abajo (OpenCV); cuaternión qw qx qy qz.
El mundo NO se normaliza ni se rota: el splat queda en metros y en los ejes de Blender, igual que el GLB del visor.
Solo numpy (funciona con el Python de Blender para probarlo en el Mac).
"""
import json, math, os, struct, sys
import numpy as np


def rot_a_quat(R):
    t = np.trace(R)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2; return np.array([0.25 * s, (R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s])
    i = int(np.argmax(np.diag(R)))
    if i == 0:
        s = math.sqrt(1 + R[0, 0] - R[1, 1] - R[2, 2]) * 2; q = [(R[2, 1] - R[1, 2]) / s, 0.25 * s, (R[0, 1] + R[1, 0]) / s, (R[0, 2] + R[2, 0]) / s]
    elif i == 1:
        s = math.sqrt(1 + R[1, 1] - R[0, 0] - R[2, 2]) * 2; q = [(R[0, 2] - R[2, 0]) / s, (R[0, 1] + R[1, 0]) / s, 0.25 * s, (R[1, 2] + R[2, 1]) / s]
    else:
        s = math.sqrt(1 + R[2, 2] - R[0, 0] - R[1, 1]) * 2; q = [(R[1, 0] - R[0, 1]) / s, (R[0, 2] + R[2, 0]) / s, (R[1, 2] + R[2, 1]) / s, 0.25 * s]
    q = np.array(q); return q if q[0] >= 0 else -q


def mundo_a_camara(c2w_gl):
    c2w = np.array(c2w_gl, np.float64) @ np.diag([1, -1, -1, 1])   # OpenGL → OpenCV
    return np.linalg.inv(c2w)


def intrinsecos(t):
    W, H = t['w'], t['h']; f = 0.5 * W / math.tan(0.5 * t['camera_angle_x'])
    return W, H, f, f, W / 2, H / 2


def convertir(datos, puntos=None):
    """Escribe el modelo en BINARIO (cameras.bin, images.bin, points3D.bin): el lector de texto de pycolmap que usa
    gsplat se detiene en la primera línea vacía y no sirve en Python 3."""
    t = json.load(open(os.path.join(datos, 'transforms.json')))
    W, H, fx, fy, cx, cy = intrinsecos(t)
    out = os.path.join(datos, 'sparse', '0'); os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'cameras.bin'), 'wb') as f:
        f.write(struct.pack('<Q', 1)); f.write(struct.pack('<iiQQ', 1, 1, W, H)); f.write(struct.pack('<4d', fx, fy, cx, cy))   # 1 = PINHOLE
    filas = []
    for fr in t['frames']:
        nombre = os.path.basename(fr['file_path'])
        if os.path.exists(os.path.join(datos, 'images', nombre)): filas.append((nombre, mundo_a_camara(fr['transform_matrix'])))   # solo vistas renderizadas
    with open(os.path.join(out, 'images.bin'), 'wb') as f:
        f.write(struct.pack('<Q', len(filas)))
        for n, (nombre, w2c) in enumerate(filas, 1):
            q = rot_a_quat(w2c[:3, :3]); tv = w2c[:3, 3]
            f.write(struct.pack('<I4d3dI', n, *q, *tv, 1)); f.write(nombre.encode() + b'\x00'); f.write(struct.pack('<Q', 0))
    puntos = puntos or os.path.join(datos, '..', 'escena', 'puntos_iniciales.txt')
    filas_p = [l.split() for l in open(puntos) if l.strip()]
    with open(os.path.join(out, 'points3D.bin'), 'wb') as f:
        f.write(struct.pack('<Q', len(filas_p)))
        for i, (x, y, z, r, g, b) in enumerate(filas_p, 1):
            f.write(struct.pack('<Q3d3BdQ', i, float(x), float(y), float(z), int(r), int(g), int(b), 0.0, 0))
    print(json.dumps({'imagenes': len(filas), 'puntos': len(filas_p), 'intrinsecos': [W, H, round(fx, 3), round(fy, 3), cx, cy], 'salida': out}))
    return len(filas)


def leer_images_bin(ruta):
    """Lector mínimo (mismo formato que pycolmap) para verificar lo escrito."""
    out = {}
    with open(ruta, 'rb') as f:
        n = struct.unpack('<Q', f.read(8))[0]
        for _ in range(n):
            d = struct.unpack('<I4d3dI', f.read(64)); nombre = b''.join(iter(lambda: f.read(1), b'\x00')).decode()
            k = struct.unpack('<Q', f.read(8))[0]; f.read(24 * k); out[nombre] = (np.array(d[1:5]), np.array(d[5:8]))
    return out


def proyectar(c2w_gl, t, P):
    """Proyecta puntos del mundo (N×3) con la convención COLMAP; devuelve píxeles (N×2) y profundidad. Para pruebas."""
    W, H, fx, fy, cx, cy = intrinsecos(t)
    w2c = mundo_a_camara(c2w_gl); Pc = P @ w2c[:3, :3].T + w2c[:3, 3]
    return np.stack([fx * Pc[:, 0] / Pc[:, 2] + cx, fy * Pc[:, 1] / Pc[:, 2] + cy], 1), Pc[:, 2]


if __name__ == '__main__':
    convertir(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
