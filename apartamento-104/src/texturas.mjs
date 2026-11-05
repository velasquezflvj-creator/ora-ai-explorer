// Texturas procedurales (sin descargas): color, relieve (normal map) y rugosidad.
// Todas son periódicas (se repiten sin costuras) y cubren paños grandes (1,2–2,4 m) para que la
// repetición no sea evidente. Las UV del GLB están en metros, así que `metros` fija la escala real.
import * as THREE from 'three';

let SIZE = 1024;
export function setTextureSize(n) { SIZE = n; }

// ---------------------------------------------------------------- ruido periódico
function mulberry(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const FIELDS = {};
function field(seed = 1, n = 256, oct = 6) {   // fbm de ruido de valor, periódico en n
  const key = seed + ':' + n + ':' + oct; if (FIELDS[key]) return FIELDS[key];
  const out = new Float32Array(n * n); const rnd = mulberry(seed * 9973);
  let amp = 1, tot = 0;
  for (let o = 0; o < oct; o++) {
    const cells = 4 << o; if (cells > n) break;
    const lat = new Float32Array(cells * cells); for (let i = 0; i < lat.length; i++) lat[i] = rnd();
    const step = n / cells;
    for (let y = 0; y < n; y++) {
      const gy = y / step, y0 = Math.floor(gy), fy = gy - y0, sy = fy * fy * (3 - 2 * fy), ya = (y0 % cells) * cells, yb = ((y0 + 1) % cells) * cells;
      for (let x = 0; x < n; x++) {
        const gx = x / step, x0 = Math.floor(gx), fx = gx - x0, sx = fx * fx * (3 - 2 * fx), xa = x0 % cells, xb = (x0 + 1) % cells;
        const a = lat[ya + xa], b = lat[ya + xb], c = lat[yb + xa], d = lat[yb + xb];
        out[y * n + x] += amp * ((a + (b - a) * sx) + ((c + (d - c) * sx) - (a + (b - a) * sx)) * sy);
      }
    }
    tot += amp; amp *= 0.5;
  }
  for (let i = 0; i < out.length; i++) out[i] /= tot;
  return (FIELDS[key] = { d: out, n });
}
function S(f, u, v) {   // muestreo bilineal periódico; u, v en píxeles del campo
  const n = f.n; u = ((u % n) + n) % n; v = ((v % n) + n) % n;
  const x0 = u | 0, y0 = v | 0, fx = u - x0, fy = v - y0, x1 = (x0 + 1) % n, y1 = (y0 + 1) % n, d = f.d;
  const a = d[y0 * n + x0], b = d[y0 * n + x1], c = d[y1 * n + x0], e = d[y1 * n + x1];
  return a + (b - a) * fx + (c - a) * fy + (a - b - c + e) * fx * fy;
}
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const mix = (a, b, t) => a + (b - a) * t;
const hex = h => { const c = new THREE.Color(h); return [c.r * 255, c.g * 255, c.b * 255]; };   // sRGB 0..255

// ---------------------------------------------------------------- lienzo → texturas three
function build(w, h, fn, { normal = 1, rough = null, metros = [1, 1], colorSpace = true } = {}) {
  const col = new Uint8ClampedArray(w * h * 4), hgt = new Float32Array(w * h), rg = rough ? new Uint8ClampedArray(w * h * 4) : null;
  const px = { r: 0, g: 0, b: 0, h: 0, ro: 0.5 };
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    px.h = 0; px.ro = rough ?? 0.5; fn(x / w, y / h, px);
    const i = (y * w + x) * 4; col[i] = px.r; col[i + 1] = px.g; col[i + 2] = px.b; col[i + 3] = 255; hgt[y * w + x] = px.h;
    if (rg) { const v = clamp(px.ro) * 255; rg[i] = rg[i + 1] = rg[i + 2] = v; rg[i + 3] = 255; }
  }
  const mk = (data, srgb) => {
    const t = new THREE.DataTexture(data, w, h, THREE.RGBAFormat); t.needsUpdate = true;
    t.wrapS = t.wrapT = THREE.RepeatWrapping; t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearMipmapLinearFilter; t.generateMipmaps = true;
    t.flipY = false; if (srgb) t.colorSpace = THREE.SRGBColorSpace; t.repeat.set(1 / metros[0], 1 / metros[1]); return t;
  };
  const out = { map: mk(col, colorSpace) };
  if (normal) {   // relieve → normal map por diferencias centrales, periódico
    const nd = new Uint8ClampedArray(w * h * 4); const k = normal * Math.max(w, h) / 256;
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const l = hgt[y * w + (x - 1 + w) % w], r = hgt[y * w + (x + 1) % w], u = hgt[((y - 1 + h) % h) * w + x], d = hgt[((y + 1) % h) * w + x];
      let nx = (l - r) * k, ny = (u - d) * k, nz = 1; const ln = Math.hypot(nx, ny, nz); nx /= ln; ny /= ln; nz /= ln;
      const i = (y * w + x) * 4; nd[i] = (nx * .5 + .5) * 255; nd[i + 1] = (ny * .5 + .5) * 255; nd[i + 2] = (nz * .5 + .5) * 255; nd[i + 3] = 255;
    }
    out.normalMap = mk(nd, false);
  }
  if (rg) out.roughnessMap = mk(rg, false);
  return out;
}
const put = (px, c, f = 1) => { px.r = c[0] * f; px.g = c[1] * f; px.b = c[2] * f; };
const lerpC = (a, b, t) => [mix(a[0], b[0], t), mix(a[1], b[1], t), mix(a[2], b[2], t)];

// ---------------------------------------------------------------- generadores
// Piso de madera en tablas de ancho `ancho` con juntas desfasadas; paño de `paño` m.
function madera({ claro, oscuro, ancho = 0.19, paño = 2.4, seed = 3, nudos = 0.25, rough = 0.55 }) {
  const N = SIZE, cols = Math.round(paño / ancho), F = field(seed), G = field(seed + 7, 256, 4), rnd = mulberry(seed);
  const cl = hex(claro), os = hex(oscuro);
  const planks = [];   // por columna: cortes (0..1) y tono de cada tabla
  for (let c = 0; c < cols; c++) {
    const cuts = []; let v = rnd(); const start = v;
    while (v < start + 1 - 0.25) { cuts.push(v % 1); v += (0.6 + rnd() * 1.1) / paño; }
    cuts.sort((a, b) => a - b); planks.push({ cuts, tones: cuts.map(() => rnd()), offs: cuts.map(() => rnd() * 256) });
  }
  return build(N, N, (u, v, px) => {
    const cf = u * cols, c = Math.floor(cf), fu = cf - c, p = planks[c];
    let k = p.cuts.length - 1; for (let i = 0; i < p.cuts.length; i++) if (v >= p.cuts[i]) k = i;
    const vStart = p.cuts[k], dv = ((v - vStart) + 1) % 1, tone = p.tones[k], off = p.offs[k];
    const grain = S(F, fu * 18 + off, dv * paño * 18 + off * 0.3);
    const rings = 0.5 + 0.5 * Math.sin((fu * 6 + S(G, off, dv * 40) * 5 + tone * 9) * 3.2);
    const streak = S(G, fu * 90 + off, v * 6);
    let t = clamp(0.15 + 0.55 * tone * 0.6 + 0.35 * grain + 0.18 * rings * grain + 0.2 * (streak - 0.5));
    let knot = 0;
    if (nudos && tone > 1 - nudos * 0.4) { const kx = (fu - 0.5) * ancho, ky = (dv - 0.35) * paño; const d = Math.hypot(kx * 2.2, ky); knot = clamp(1 - d / 0.035); }
    t = clamp(t + knot * 0.6);
    put(px, lerpC(cl, os, t));
    const edge = Math.min(fu, 1 - fu) * ancho, jEnd = Math.min(dv, 1 - dv) * paño;
    let h = 0.4 * grain + 0.15 * rings - knot * 0.3;
    if (edge < 0.0015 || jEnd < 0.0012) { h -= 1.6; put(px, lerpC(cl, os, 0.95), 0.75); }
    else if (edge < 0.003) h -= 0.6;
    px.h = h; px.ro = rough + (tone - 0.5) * 0.12 + (grain - 0.5) * 0.15;
  }, { normal: 1.1, rough, metros: [paño, paño] });
}

// Losas de piedra o porcelanato de `lx` × `ly` m con vetas suaves.
function piedra({ base, veta, lx = 0.6, ly = 1.2, paño = 2.4, vetas = 0.35, seed = 11, junta = '#9a948a', rough = 0.35, escala = 1 }) {
  const N = SIZE, F = field(seed), G = field(seed + 3, 256, 5), rnd = mulberry(seed);
  const b = hex(base), vv = hex(veta), j = hex(junta);
  const nx = Math.round(paño / lx), ny = Math.round(paño / ly); const offs = Array.from({ length: nx * ny * 2 }, () => [rnd() * 256, rnd() * 256, rnd()]);
  return build(N, N, (u, v, px) => {
    const row = Math.floor(v * ny), shift = (row % 2) * 0.5 / nx, uu = (u + shift) % 1, col = Math.floor(uu * nx);
    const o = offs[(row * nx + col) % offs.length];
    const fx = uu * nx - col, fy = v * ny - row;
    const x = (fx * lx) * 60 * escala + o[0], y = (fy * ly) * 60 * escala + o[1];
    const w = S(F, x * 0.8, y * 0.8);
    const vein = Math.pow(1 - Math.abs(Math.sin((x * 0.05 + y * 0.02 + w * 6) * 2.2)), 18) * vetas;
    const cloud = S(G, x * 2, y * 2);
    const tone = (o[2] - 0.5) * 0.06;
    put(px, lerpC(b, vv, clamp(vein + (cloud - 0.5) * 0.35 + tone)));
    const ex = Math.min(fx, 1 - fx) * lx, ey = Math.min(fy, 1 - fy) * ly;
    px.h = cloud * 0.15 + vein * 0.2;
    px.ro = rough + (cloud - 0.5) * 0.1;
    if (ex < 0.0016 || ey < 0.0016) { put(px, j); px.h = -1.2; px.ro = 0.9; }
  }, { normal: 0.9, rough, metros: [paño, paño] });
}

// Mármol o cuarzo continuo (mesones, salpicaderos de losa).
function marmol({ base, veta, veta2 = null, intensidad = 1, seed = 21, paño = 1.6, rough = 0.18, grano = 0 }) {
  const N = SIZE, F = field(seed), G = field(seed + 5, 256, 6), H = field(seed + 9, 256, 3);
  const b = hex(base), v1 = hex(veta), v2 = veta2 ? hex(veta2) : v1;
  return build(N, N, (u, v, px) => {
    const x = u * 256, y = v * 256;
    const w = S(F, x, y), w2 = S(H, x * 0.5, y * 0.5);
    const main = Math.pow(1 - Math.abs(Math.sin((u * 2 + v * 1 + w * 3.5) * Math.PI * 2)), 26) * intensidad;
    const fine = Math.pow(1 - Math.abs(Math.sin((u * 5 - v * 3 + S(G, x * 2, y * 2) * 4) * Math.PI * 2)), 40) * 0.6 * intensidad;
    const cloud = S(G, x * 3, y * 3);
    let c = lerpC(b, v2, clamp(fine + (w2 - 0.5) * 0.25 * intensidad));
    c = lerpC(c, v1, clamp(main));
    if (grano) { const sp = S(G, x * 23, y * 23); if (sp > 0.72) c = lerpC(c, v1, grano * (sp - 0.72) * 3); else if (sp < 0.3) c = lerpC(c, [255, 255, 255], grano * 0.5); }
    put(px, c, 1 + (cloud - 0.5) * 0.05);
    px.h = cloud * 0.08; px.ro = rough + (cloud - 0.5) * 0.06;
  }, { normal: 0.3, rough, metros: [paño, paño] });
}

// Microcemento: nubes de bajo contraste y huellas de llana.
function microcemento({ base, sombra, seed = 31, paño = 2.4, rough = 0.6 }) {
  const N = SIZE, F = field(seed), G = field(seed + 2, 256, 6);
  const b = hex(base), s = hex(sombra);
  return build(N, N, (u, v, px) => {
    const x = u * 256, y = v * 256;
    const c = S(F, x * 2, y * 2), t = S(G, x * 6 + S(F, x, y) * 30, y * 1.5);
    put(px, lerpC(b, s, clamp((c - 0.5) * 1.3 + 0.35 + (t - 0.5) * 0.25)));
    px.h = c * 0.3 + t * 0.15; px.ro = rough + (c - 0.5) * 0.18;
  }, { normal: 0.5, rough, metros: [paño, paño] });
}

// Baldosa o enchape esmaltado de `lx` × `ly` m con variación por pieza.
function baldosa({ base, base2 = null, lx = 0.3, ly = 0.6, junta = '#cfc9be', variacion = 0.05, seed = 41, paño = 1.2, ondas = 0.4, rough = 0.2, trabada = false, vetas = 0 }) {
  const N = SIZE >> 1, F = field(seed), rnd = mulberry(seed);
  const b = hex(base), b2 = hex(base2 || base), j = hex(junta);
  const nx = Math.round(paño / lx), ny = Math.round(paño / ly); const tones = Array.from({ length: nx * ny + nx }, () => [rnd(), rnd() * 256, rnd() * 256]);
  return build(N, N, (u, v, px) => {
    const row = Math.floor(v * ny), shift = trabada ? (row % 2) * 0.5 / nx : 0, uu = (u + shift) % 1, col = Math.floor(uu * nx);
    const o = tones[row * nx + col]; const fx = uu * nx - col, fy = v * ny - row;
    const w = S(F, fx * 40 + o[1], fy * 40 * ly / lx + o[2]);
    let c = lerpC(b, b2, o[0]);
    if (vetas) c = lerpC(c, hex('#8d877c'), Math.pow(1 - Math.abs(Math.sin((fx * 2 + fy + w * 3) * 6)), 20) * vetas);
    put(px, c, 1 + (o[0] - 0.5) * variacion + (w - 0.5) * 0.05);
    const ex = Math.min(fx, 1 - fx) * lx, ey = Math.min(fy, 1 - fy) * ly;
    const bevel = Math.min(1, Math.min(ex, ey) / 0.004);
    px.h = bevel * (0.6 + w * ondas); px.ro = rough + (w - 0.5) * 0.08;
    if (ex < 0.0015 || ey < 0.0015) { put(px, j); px.h = -0.5; px.ro = 0.85; }
  }, { normal: 1.2, rough, metros: [paño, paño] });
}

// Enchapado de madera para muebles: veta continua.
function chapa({ claro, oscuro, seed = 51, paño = 1.2, rough = 0.5, contraste = 1 }) {
  const N = SIZE >> 1, F = field(seed), G = field(seed + 4, 256, 4);
  const cl = hex(claro), os = hex(oscuro);
  return build(N, N, (u, v, px) => {
    const x = u * 256, y = v * 256;
    const w = S(F, x * 3, y * 0.4);
    const rings = 0.5 + 0.5 * Math.sin((u * 14 + w * 6) * Math.PI * 2);
    const t = clamp(0.3 + (w - 0.5) * 0.9 * contraste + rings * 0.25 * contraste + (S(G, x * 30, y * 2) - 0.5) * 0.3);
    put(px, lerpC(cl, os, t)); px.h = w * 0.3 + rings * 0.1; px.ro = rough + (w - 0.5) * 0.1;
  }, { normal: 0.4, rough, metros: [paño, paño] });
}

// Tela: trama fina + moteado.
function tela({ base, seed = 61, paño = 0.5, trama = 1, moteado = 0.12 }) {
  const N = SIZE >> 1, F = field(seed, 256, 5), b = hex(base);
  const k = 220 * paño / 0.5;
  return build(N, N, (u, v, px) => {
    const wx = Math.sin(u * k * Math.PI * 2), wy = Math.sin(v * k * Math.PI * 2);
    const weave = (wx * 0.5 + 0.5) * ((Math.floor(v * k * 2) % 2) ? 1 : 0.6) + (wy * 0.5 + 0.5) * ((Math.floor(u * k * 2) % 2) ? 0.6 : 1);
    const m = S(F, u * 256 * 2, v * 256 * 2);
    put(px, b, 1 - moteado * 0.5 + (m - 0.5) * moteado + weave * 0.04 * trama);
    px.h = weave * 0.35 * trama + m * 0.2;
  }, { normal: 0.9, metros: [paño, paño] });
}

// Pintura sobre pañete: relieve muy suave (evita el aspecto plástico).
function pintura({ seed = 71 }) {
  const N = SIZE >> 1, F = field(seed, 256, 6), G = field(seed + 1, 256, 3);
  return build(N, N, (u, v, px) => {
    const a = S(F, u * 256 * 3, v * 256 * 3), b = S(G, u * 256, v * 256);
    const c = 246 + (a - 0.5) * 10 + (b - 0.5) * 6; px.r = px.g = px.b = c;   // se multiplica por el color del muro
    px.h = a * 0.25 + b * 0.1;
  }, { normal: 0.35, metros: [1.6, 1.6] });
}

// Tapete de lana con patrón suave.
function tapete({ base, linea, seed = 81 }) {
  const N = SIZE >> 1, F = field(seed, 256, 6), b = hex(base), l = hex(linea);
  return build(N, N, (u, v, px) => {
    const m = S(F, u * 256 * 6, v * 256 * 6), q = S(F, u * 256 * 0.8, v * 256 * 0.8);
    const pat = Math.abs(Math.sin(u * Math.PI * 10 + q * 3)) < 0.05 || Math.abs(Math.sin(v * Math.PI * 10 + q * 3)) < 0.05;
    put(px, pat ? l : b, 0.92 + m * 0.16); px.h = m;
  }, { normal: 1.5, metros: [1.0, 1.0] });
}

// Deck exterior de madera (balcón propuesto).
function deck({ claro, oscuro, seed = 91 }) {
  const N = SIZE >> 1, F = field(seed), rnd = mulberry(seed), cl = hex(claro), os = hex(oscuro); const tones = Array.from({ length: 20 }, () => rnd());
  return build(N, N, (u, v, px) => {
    const cols = 10, c = Math.floor(u * cols), fu = u * cols - c;
    const g = S(F, fu * 14 + c * 31, v * 160);
    put(px, lerpC(cl, os, clamp(tones[c] * 0.4 + g * 0.6)));
    px.h = g * 0.3; px.ro = 0.75;
    if (fu < 0.05 || fu > 0.95) { put(px, [40, 32, 26]); px.h = -2; }
  }, { normal: 1.2, rough: 0.75, metros: [1.4, 1.4] });
}

// Cuadro abstracto (UV 0..1): manchas y arcos en la paleta del acabado.
function cuadro({ fondo, a, b, c, seed = 101 }) {
  const N = 512, F = field(seed, 256, 5), f = hex(fondo), A = hex(a), B = hex(b), C = hex(c);
  return build(N, N, (u, v, px) => {
    const w = S(F, u * 256, v * 256);
    let col = f;
    const d1 = Math.hypot(u - 0.35, v - 0.55); if (d1 < 0.26 + (w - 0.5) * 0.04) col = A;
    if (u > 0.5 && u < 0.78 && v > 0.18 + (w - .5) * 0.03 && v < 0.82) col = B;
    const d2 = Math.abs(Math.hypot(u - 0.7, v - 0.25) - 0.18); if (d2 < 0.012) col = C;
    put(px, col, 0.95 + w * 0.1); px.h = w * 0.5;
  }, { normal: 0.6, metros: [1, 1] });
}

// Pasto del entorno conceptual.
function pasto({ seed = 111 }) {
  const N = 512, F = field(seed, 256, 6), G = field(seed + 1, 256, 3);
  const a = hex('#7c9757'), b = hex('#9aac63'), c = hex('#5b7546');
  return build(N, N, (u, v, px) => {
    const x = u * 256, y = v * 256, n = S(F, x * 8, y * 8), m = S(G, x, y);
    const stripe = 0.5 + 0.5 * Math.sin(u * Math.PI * 6);   // franjas de corte suaves
    put(px, lerpC(lerpC(c, a, n), b, clamp((m - 0.45) * 2 + stripe * 0.12)), 0.92 + S(F, x * 40, y * 40) * 0.16); px.h = n + S(F, x * 40, y * 40);
  }, { normal: 1.4, metros: [9, 9] });
}

export const GEN = { madera, piedra, marmol, microcemento, baldosa, chapa, tela, pintura, tapete, deck, cuadro, pasto };
const CACHE = {};
// Devuelve (y guarda) el juego de texturas de una receta {gen, ...parámetros}.
export function textura(id, receta) {
  if (!CACHE[id]) { const { gen, ...p } = receta; CACHE[id] = GEN[gen](p); }
  return CACHE[id];
}
export function anisotropy(r) { const a = Math.min(8, r.capabilities.getMaxAnisotropy()); for (const t of Object.values(CACHE)) for (const m of Object.values(t)) m.anisotropy = a; return a; }
export const cacheSize = () => Object.keys(CACHE).length;
