// Splat SINTÉTICO para probar el visor antes de pagar la nube (no es el resultado del piloto ni se parece a Cycles):
// convierte la nube de puntos inicial (superficies reales del modelo, ejes de Blender) en gaussianas pequeñas en
// formato PLY de 3DGS. Sirve para verificar carga, orientación, alineación con la malla y fps con N gaussianas.
//   node tools/splat/ply_sintetico.mjs <puntos_iniciales.txt> <salida.ply> [millones=0.25] [--parche]
// Con N mayor que los puntos disponibles, repite cada punto con un desplazamiento de ±1 cm sobre la superficie
// (simula la densidad de un splat real de 1–3 M). --parche añade un cuadro de color conocido (sRGB 200,100,50) de
// 40 × 40 cm, vertical, en x = −2,0 m, y = 0, z = 1,0–1,4 m (Blender) para calibrar el color en pantalla.
import { readFileSync, writeFileSync } from 'node:fs';

const [entrada, salida, millones = '0.25'] = process.argv.slice(2);
const parche = process.argv.includes('--parche');
const filas = readFileSync(entrada, 'utf8').trim().split('\n').map(l => l.split(' ').map(Number));
const N = Math.round(Number(millones) * 1e6);
const pts = [];
let semilla = 102; const rnd = () => ((semilla = (semilla * 1664525 + 1013904223) >>> 0) / 4294967296);
for (let i = 0; i < N; i++) {
  const [x, y, z, r, g, b] = filas[i % filas.length], k = i < filas.length ? 0 : 0.01;
  pts.push([x + (rnd() - 0.5) * 2 * k, y + (rnd() - 0.5) * 2 * k, z + (rnd() - 0.5) * 2 * k, r, g, b, 0.012]);
}
if (parche) for (let i = 0; i < 40; i++) for (let j = 0; j < 40; j++) pts.push([-2.0, -0.2 + i * 0.01, 1.0 + j * 0.01, 200, 100, 50, 0.008]);
const C0 = 0.28209479177387814, props = ['x', 'y', 'z', 'f_dc_0', 'f_dc_1', 'f_dc_2', 'opacity', 'scale_0', 'scale_1', 'scale_2', 'rot_0', 'rot_1', 'rot_2', 'rot_3'];
const cab = `ply\nformat binary_little_endian 1.0\nelement vertex ${pts.length}\n${props.map(p => `property float ${p}`).join('\n')}\nend_header\n`;
const buf = Buffer.alloc(cab.length + pts.length * props.length * 4); buf.write(cab, 0, 'ascii');
let o = cab.length;
const w = v => { buf.writeFloatLE(v, o); o += 4; };
for (const [x, y, z, r, g, b, s] of pts) {
  w(x); w(y); w(z); w((r / 255 - 0.5) / C0); w((g / 255 - 0.5) / C0); w((b / 255 - 0.5) / C0);
  w(Math.log(0.97 / 0.03)); w(Math.log(s)); w(Math.log(s)); w(Math.log(s)); w(1); w(0); w(0); w(0);
}
writeFileSync(salida, buf);
console.log(JSON.stringify({ salida, gaussianas: pts.length, mb: +(buf.length / 1e6).toFixed(1), parche }));
