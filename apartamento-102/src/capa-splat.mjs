// Piloto de Gaussian Splatting sobre la V5, sin modificar la V5: este módulo se empaqueta JUNTO a
// src/app-recorrido-v5.mjs (una sola copia de three) en dist/recorrido-splat-app.js y usa solo lo que la V5 expone
// (window.__ORA: renderer, scene, camera, composer; window.APTO_API).
//
//  - Carga el splat (Spark 2.4.0, MIT) desde ?splat=<url> (por defecto modelo/web/splat/splat_sala_cocina.ply).
//  - El splat se entrenó en metros y en los ejes de Blender (Z arriba): aquí se gira −90° en X para pasar a los ejes de
//    three (Y arriba), igual que el GLB exportado desde Blender. Mismo origen: no hay traslación.
//  - Navegación y colisiones son las de la V5 (se calculan con la planta, no con las mallas): siguen activas.
//  - Modo «splat»: la cámara ve solo la capa 5 (el splat). Las imágenes de entrenamiento ya traen la vista AgX de
//    Blender, así que se dibuja directo a pantalla sin la cadena de posproceso (TAA, GTAO, resplandor, tabla AgX).
//  - Tecla M (o botón): alterna splat ↔ malla V5 desde la misma posición, para comparar.
import * as THREE from 'three';
import { SparkRenderer, SplatMesh } from '@sparkjsdev/spark';

const CAPA = 5;
const params = new URLSearchParams(location.search);
const URL_SPLAT = params.get('splat') || 'modelo/web/splat/splat_sala_cocina.ply';
const estado = { cargado: false, error: null, activo: params.get('modo') !== 'malla', gaussianas: 0, ms_carga: 0, bytes: 0 };

function esperar(cond) { return new Promise(r => { const f = () => (cond() ? r() : setTimeout(f, 50)); f(); }); }

(async () => {
await esperar(() => window.APTO_API?.ready && window.__ORA);
const { renderer, scene, camera } = window.__ORA;
const poke = n => window.APTO_API.render(n);

const spark = new SparkRenderer({ renderer, onDirty: () => poke(2), preBlurAmount: Number(params.get('preblur') ?? 0.3) });
spark.layers.set(CAPA); scene.add(spark);

const t0 = performance.now();
let splat;
try {
  const resp = await fetch(URL_SPLAT);
  if (!resp.ok) throw new Error(`${resp.status} ${URL_SPLAT}`);
  const bytes = new Uint8Array(await resp.arrayBuffer()); estado.bytes = bytes.byteLength;
  splat = new SplatMesh({ fileBytes: bytes, fileName: URL_SPLAT.split('/').pop() });
  await splat.initialized;
  splat.quaternion.setFromAxisAngle(new THREE.Vector3(1, 0, 0), -Math.PI / 2);   // Blender (Z arriba) → three (Y arriba)
  splat.layers.set(CAPA); scene.add(splat);
  estado.cargado = true; estado.gaussianas = splat.packedSplats?.numSplats ?? 0;
} catch (e) { estado.error = String(e?.message || e); console.error('[splat]', e); }
estado.ms_carga = Math.round(performance.now() - t0);

// render directo a pantalla en modo splat (la V5 rehace su composer al cambiar de calidad: se revisa cada cuadro)
const parcheados = new WeakSet();
function parchear() {
  const c = window.__ORA.composer;
  if (c && !parcheados.has(c)) {
    const original = c.render.bind(c);
    c.render = dt => {
      if (!(estado.activo && estado.cargado)) return original(dt);
      const tm = renderer.toneMapping; renderer.toneMapping = THREE.NoToneMapping;
      renderer.setRenderTarget(null); renderer.render(scene, camera); renderer.toneMapping = tm;
    };
    parcheados.add(c);
  }
  requestAnimationFrame(parchear);
}
parchear();

function aplicar() {
  if (estado.activo && estado.cargado) camera.layers.set(CAPA); else camera.layers.set(0);
  const b = document.getElementById('btnSplat');
  if (b) { b.textContent = estado.activo ? 'Ver malla V5 (M)' : 'Ver splat (M)'; b.setAttribute('aria-pressed', String(estado.activo)); }
  const i = document.getElementById('splatInfo');
  if (i) i.textContent = estado.error ? `Splat no disponible: ${estado.error}` : `${estado.activo ? 'Splat' : 'Malla V5'} · ${(estado.gaussianas / 1e6).toFixed(2)} M gaussianas · ${(estado.bytes / 1e6).toFixed(0)} MB`;
  poke(6);
}
function alternar() { estado.activo = !estado.activo; aplicar(); }
addEventListener('keydown', e => { if (e.key === 'm' || e.key === 'M') alternar(); });
document.getElementById('btnSplat')?.addEventListener('click', alternar);
aplicar();

window.SPLAT_API = {
  get estado() { return { ...estado }; },
  activar: on => { estado.activo = !!on; aplicar(); },
};
})();
