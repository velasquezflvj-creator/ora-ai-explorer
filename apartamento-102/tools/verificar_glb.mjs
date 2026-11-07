// Verifica que un GLB derivado conserve la arquitectura del original: mismos nodos, metadatos (extras), materiales y
// exactamente las mismas posiciones de vértices en coordenadas de mundo (tolerancia 0,1 mm). Un GLB derivado puede
// tener más vértices (p. ej. por las costuras de un segundo juego de UV), pero no posiciones nuevas ni distintas.
//   node apartamento-102/tools/verificar_glb.mjs apartamento-102/modelo/apto-102-propuesta.glb apartamento-102/modelo/web/v4/apto-102-v4.glb
import { readFileSync } from 'node:fs';

const leer = ruta => {
  const b = readFileSync(ruta); const jl = b.readUInt32LE(12); const json = JSON.parse(b.subarray(20, 20 + jl).toString('utf8'));
  const bin = b.subarray(20 + jl + 8); return { json, bin };
};
const COMP = { 5126: [Float32Array, 4], 5125: [Uint32Array, 4], 5123: [Uint16Array, 2], 5121: [Uint8Array, 1] };
const NC = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4 };
function accesor({ json, bin }, i) {
  const a = json.accessors[i], v = json.bufferViews[a.bufferView], [T, sz] = COMP[a.componentType], n = NC[a.type];
  const off = (v.byteOffset || 0) + (a.byteOffset || 0), stride = v.byteStride || sz * n, out = new Float64Array(a.count * n);
  for (let k = 0; k < a.count; k++) for (let c = 0; c < n; c++) {
    const p = off + k * stride + c * sz;
    out[k * n + c] = a.componentType === 5126 ? bin.readFloatLE(p) : a.componentType === 5125 ? bin.readUInt32LE(p) : a.componentType === 5123 ? bin.readUInt16LE(p) : bin.readUInt8(p);
  }
  return out;
}
const mul = (a, b) => { const o = new Array(16).fill(0); for (let r = 0; r < 4; r++) for (let c = 0; c < 4; c++) for (let k = 0; k < 4; k++) o[c * 4 + r] += a[k * 4 + r] * b[c * 4 + k]; return o; };
function local(n) {
  if (n.matrix) return n.matrix;
  const [x, y, z, w] = n.rotation || [0, 0, 0, 1], [sx, sy, sz] = n.scale || [1, 1, 1], [tx, ty, tz] = n.translation || [0, 0, 0];
  return [(1 - 2 * (y * y + z * z)) * sx, 2 * (x * y + z * w) * sx, 2 * (x * z - y * w) * sx, 0,
    2 * (x * y - z * w) * sy, (1 - 2 * (x * x + z * z)) * sy, 2 * (y * z + x * w) * sy, 0,
    2 * (x * z + y * w) * sz, 2 * (y * z - x * w) * sz, (1 - 2 * (x * x + y * y)) * sz, 0, tx, ty, tz, 1];
}
function analizar(g) {
  const r = {}, I = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
  const visitar = (i, M) => {
    const n = g.json.nodes[i], W = mul(M, local(n));
    const e = { extras: JSON.stringify(n.extras ?? null), pos: new Set(), mats: new Set(), uv1: false, min: [Infinity, Infinity, Infinity], max: [-Infinity, -Infinity, -Infinity] };
    if (n.mesh !== undefined) for (const p of g.json.meshes[n.mesh].primitives) {
      const P = accesor(g, p.attributes.POSITION);
      for (let k = 0; k < P.length; k += 3) {
        const x = W[0] * P[k] + W[4] * P[k + 1] + W[8] * P[k + 2] + W[12], y = W[1] * P[k] + W[5] * P[k + 1] + W[9] * P[k + 2] + W[13], z = W[2] * P[k] + W[6] * P[k + 1] + W[10] * P[k + 2] + W[14];
        e.pos.add(`${Math.round(x * 1e4)},${Math.round(y * 1e4)},${Math.round(z * 1e4)}`);
        [x, y, z].forEach((v, c) => { e.min[c] = Math.min(e.min[c], v); e.max[c] = Math.max(e.max[c], v); });
      }
      if (p.material !== undefined) e.mats.add(g.json.materials[p.material].name);
      if (p.attributes.TEXCOORD_1 !== undefined) e.uv1 = true;
    }
    r[n.name] = e; for (const c of n.children || []) visitar(c, W);
  };
  for (const i of g.json.scenes[g.json.scene || 0].nodes) visitar(i, I);
  return r;
}
const [fa, fb] = process.argv.slice(2);
const A = analizar(leer(fa)), B = analizar(leer(fb));
const problemas = [];
const na = Object.keys(A).sort(), nb = Object.keys(B).sort();
if (JSON.stringify(na) !== JSON.stringify(nb)) problemas.push({ nodos: { solo_original: na.filter(n => !B[n]), solo_derivado: nb.filter(n => !A[n]) } });
let vertices = 0, conUv1 = 0;
for (const n of na) {
  if (!B[n]) continue;
  const a = A[n], b = B[n];
  if (a.extras !== b.extras) problemas.push({ nodo: n, extras: 'distintos' });
  if ([...a.mats].sort().join() !== [...b.mats].sort().join()) problemas.push({ nodo: n, materiales: [[...a.mats], [...b.mats]] });
  const faltan = [...a.pos].filter(p => !b.pos.has(p)).length, sobran = [...b.pos].filter(p => !a.pos.has(p)).length;
  if (faltan || sobran) {
    // caja envolvente en mm: un bisel o un objeto decorativo reemplazado no deben cambiar las dimensiones exteriores
    const dif_mm = Math.max(...[0, 1, 2].map(c => Math.max(Math.abs(a.min[c] - b.min[c]), Math.abs(a.max[c] - b.max[c])))) * 1000;
    problemas.push({ nodo: n, posiciones_faltantes: faltan, posiciones_nuevas: sobran, caja_envolvente_dif_mm: +dif_mm.toFixed(2) });
  }
  vertices += a.pos.size; if (b.uv1) conUv1++;
}
console.log(JSON.stringify({ original: fa, derivado: fb, nodos: na.length, posiciones_unicas_comparadas: vertices, nodos_con_uv1: conUv1, problemas, resultado: problemas.length ? 'DIFERENTE' : 'IDÉNTICO en arquitectura (nodos, extras, materiales y posiciones)' }, null, 1));
process.exit(problemas.length ? 1 : 0);
