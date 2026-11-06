// Entorno exterior CONCEPTUAL: cielo físico, jardín con pinos, colinas y volúmenes lejanos.
// No representa la vista real del proyecto ni el nivel real del terreno; el visor lo rotula así.
import * as THREE from 'three';
import { Sky } from 'three/addons/objects/Sky.js';
import { textura } from './texturas.mjs';

export const NIVEL_TERRENO = -3.2;   // supuesto conceptual: el apartamento se ve a un nivel sobre un jardín

function mulberry(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

export function crearEntorno({ sunDir, W, H, balcon }) {
  const g = new THREE.Group(); g.name = 'ENTORNO_conceptual';
  const rnd = mulberry(104);
  const Y = NIVEL_TERRENO;

  // cielo físico (Preetham) alineado con el sol del visor
  const sky = new Sky(); sky.scale.setScalar(900);
  const u = sky.material.uniforms;
  u.turbidity.value = 5.5; u.rayleigh.value = 1.1; u.mieCoefficient.value = 0.004; u.mieDirectionalG.value = 0.82;
  u.sunPosition.value.copy(sunDir).multiplyScalar(400);
  g.add(sky);

  // jardín
  const grass = textura('pasto', { gen: 'pasto' });
  const lawnMat = new THREE.MeshLambertMaterial({ map: grass.map });
  for (const t of [lawnMat.map]) t.repeat.set(1 / 9, 1 / 9);
  const lawnGeo = new THREE.CircleGeometry(320, 96); lawnGeo.rotateX(-Math.PI / 2);
  const uv = lawnGeo.attributes.uv, pos = lawnGeo.attributes.position;
  for (let i = 0; i < uv.count; i++) uv.setXY(i, pos.getX(i), pos.getZ(i));   // UV en metros
  const lawn = new THREE.Mesh(lawnGeo, lawnMat); lawn.position.y = Y; lawn.receiveShadow = true; g.add(lawn);

  // zócalo bajo el apartamento (conceptual) y sendero de piedra
  const conc = new THREE.MeshLambertMaterial({ color: '#cfcac1' });
  const zocalo = new THREE.Mesh(new THREE.BoxGeometry(W + 0.02, -0.13 - Y, H + 0.02), conc);
  zocalo.position.set(0, (Y - 0.13) / 2, 0); zocalo.receiveShadow = true; g.add(zocalo);
  const banda = new THREE.Mesh(new THREE.BoxGeometry(W + 0.06, 0.12, H + 0.06), new THREE.MeshLambertMaterial({ color: '#8e8a83' }));
  banda.position.y = -0.19; g.add(banda);
  const path = new THREE.Mesh(new THREE.PlaneGeometry(2.2, 60), new THREE.MeshLambertMaterial({ color: '#c9c0b0' }));
  path.rotation.x = -Math.PI / 2; path.position.set(-6.5, Y + 0.01, 24); path.receiveShadow = true; g.add(path);

  // galería de acceso conceptual frente a la puerta principal (el DWG del apartamento no la incluye)
  const gal = new THREE.Group(); gal.name = 'ENTORNO_galeria';
  const gw = 16, gd = 1.6, gx = 0.2, gz = -H / 2 - gd / 2;   // al norte del apartamento (Z negativo)
  const piso = new THREE.Mesh(new THREE.BoxGeometry(gw, 0.14, gd), new THREE.MeshLambertMaterial({ color: '#cbc5bb' }));
  piso.position.set(gx, -0.07, gz); piso.receiveShadow = true; gal.add(piso);
  const losa = new THREE.Mesh(new THREE.BoxGeometry(gw, 0.14, gd + 0.3), new THREE.MeshLambertMaterial({ color: '#f1efea' }));
  losa.position.set(gx, 2.47, gz - 0.15); losa.castShadow = true; gal.add(losa);
  const baranda = new THREE.Mesh(new THREE.BoxGeometry(gw, 0.05, 0.05), new THREE.MeshLambertMaterial({ color: '#3a3a3c' }));
  baranda.position.set(gx, 1.0, gz - gd / 2 + 0.03); gal.add(baranda);
  for (let x = -7; x <= 8; x += 1.5) { const p = new THREE.Mesh(new THREE.BoxGeometry(0.03, 1.0, 0.03), baranda.material); p.position.set(x, 0.5, gz - gd / 2 + 0.03); gal.add(p); }
  const muroMat = new THREE.MeshLambertMaterial({ color: '#e7e3dc' });
  for (const [x0, x1] of [[gx - gw / 2, -W / 2], [W / 2, gx + gw / 2]]) {   // fachada de acceso de las unidades vecinas (fuera del apartamento)
    const mw = new THREE.Mesh(new THREE.BoxGeometry(x1 - x0, 2.4, 0.15), muroMat); mw.position.set((x0 + x1) / 2, 1.2, -H / 2 + 0.075); gal.add(mw);
  }
  const luzGal = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.02, 0.12), new THREE.MeshBasicMaterial({ color: '#fff1d8' }));
  luzGal.position.set(-W / 2 + 0.65, 2.39, gz); gal.add(luzGal);
  g.add(gal);

  // setos bajos y arbustos cerca de la fachada
  const hedgeMat = new THREE.MeshLambertMaterial({ color: '#4d6a3c' });
  const hedgeGeo = new THREE.BoxGeometry(1, 1, 1);
  for (const [x, z, w, d, h] of [[0, 7.2, 12, 0.9, 1.0], [-7.2, 0, 0.9, 10, 1.0], [7.4, 1, 0.9, 12, 1.0], [-2, 13, 6, 0.8, 0.8]]) {
    const m = new THREE.Mesh(hedgeGeo, hedgeMat); m.scale.set(w, h, d); m.position.set(x, Y + h / 2, z); m.castShadow = m.receiveShadow = true; g.add(m);
  }
  // arbustos orgánicos (icosaedro deformado, sombreado suave)
  const bushGeo = new THREE.IcosahedronGeometry(1, 4); const bp = bushGeo.attributes.position;
  for (let i = 0; i < bp.count; i++) { const v = new THREE.Vector3().fromBufferAttribute(bp, i); const k = 0.82 + 0.3 * Math.abs(Math.sin(v.x * 5.1 + v.y * 3.7) * Math.cos(v.z * 4.3)); bp.setXYZ(i, v.x * k, v.y * k, v.z * k); }
  bushGeo.computeVertexNormals();
  const NB = 34;
  const bushes = new THREE.InstancedMesh(bushGeo, new THREE.MeshLambertMaterial({ color: '#ffffff' }), NB);
  const M = new THREE.Matrix4(), q = new THREE.Quaternion(), s = new THREE.Vector3(), p = new THREE.Vector3(), c = new THREE.Color();
  for (let i = 0; i < NB; i++) {
    const a = rnd() * Math.PI * 2, r = 6.5 + rnd() * 10;
    p.set(Math.cos(a) * r, Y + 0.25, Math.sin(a) * r + 2); if (Math.abs(p.x) < 5.5 && p.z > -5 && p.z < 6.5) p.z += 8;
    const k = 0.45 + rnd() * 0.75; s.set(k * 1.3, k * 0.85, k * 1.1);
    q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), rnd() * 6); M.compose(p, q, s); bushes.setMatrixAt(i, M);
    bushes.setColorAt(i, c.setHSL(0.22 + rnd() * 0.08, 0.38, 0.27 + rnd() * 0.1));
  }
  bushes.castShadow = true; bushes.receiveShadow = true; g.add(bushes);

  // pinos: tronco + cinco verticilos cónicos con sombreado suave; un anillo cercano y una franja lejana
  function pinos(N, rMin, rMax, hMin, hMax, tiersN, seg) {
    const trunk = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.1, 0.22, 1, 8), new THREE.MeshLambertMaterial({ color: '#4f3b2d' }), N);
    const cg = new THREE.ConeGeometry(1, 1, seg, 1, true); const cp = cg.attributes.position;
    for (let i = 0; i < cp.count; i++) { const y = cp.getY(i); if (y < 0) { const ang = Math.atan2(cp.getZ(i), cp.getX(i)); const k = 1 + 0.12 * Math.sin(ang * 7); cp.setX(i, cp.getX(i) * k); cp.setZ(i, cp.getZ(i) * k); cp.setY(i, y - 0.08 * Math.abs(Math.sin(ang * 3.5))); } }
    cg.computeVertexNormals();
    const crownMat = new THREE.MeshLambertMaterial({ color: '#ffffff', side: THREE.DoubleSide });
    const tiers = Array.from({ length: tiersN }, () => new THREE.InstancedMesh(cg, crownMat, N));
    let n = 0;
    while (n < N) {
      const a = rnd() * Math.PI * 2, r = rMin + Math.pow(rnd(), 0.8) * (rMax - rMin);
      const x = Math.cos(a) * r, z = Math.sin(a) * r;
      if (z > 4 && Math.abs(x - 1) < 6 + z * 0.15 && z < 34) continue;   // deja abierta la vista frontal del balcón
      if (Math.abs(x) < 8 && Math.abs(z) < 8) continue;
      const h = hMin + rnd() * (hMax - hMin), w = h * (0.2 + rnd() * 0.06), rot = rnd() * 6;
      q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), rot);
      M.compose(p.set(x, Y + h * 0.3, z), q, s.set(1 + h * 0.02, h * 0.6, 1 + h * 0.02)); trunk.setMatrixAt(n, M);
      const hue = 0.28 + rnd() * 0.05, sat = 0.28 + rnd() * 0.12, lum = 0.19 + rnd() * 0.07;
      tiers.forEach((t, k) => {
        const f = k / (tiersN - 1), ww = w * (1 - f * 0.75), hh = h * (0.34 - f * 0.12), yy = Y + h * (0.3 + f * 0.62) + hh / 2;
        M.compose(p.set(x, yy, z), q, s.set(ww, hh, ww)); t.setMatrixAt(n, M); t.setColorAt(n, c.setHSL(hue, sat, lum + f * 0.05));
      });
      n++;
    }
    trunk.castShadow = true; g.add(trunk); tiers.forEach(t => { t.castShadow = rMin < 30; g.add(t); });
  }
  pinos(70, 9, 70, 10, 19, 5, 14);
  pinos(260, 80, 230, 12, 24, 3, 8);
  // un par de árboles de hoja ancha junto al jardín
  const leafGeo = new THREE.IcosahedronGeometry(1, 2); leafGeo.computeVertexNormals();
  const leafMat = new THREE.MeshLambertMaterial({ color: '#58733f' });
  for (const [x, z, h] of [[-9.5, 9, 7], [11, 6.5, 8], [-12, -4, 6.5]]) {
    const tr = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.24, h * 0.55, 8), new THREE.MeshLambertMaterial({ color: '#5b4637' }));
    tr.position.set(x, Y + h * 0.275, z); tr.castShadow = true; g.add(tr);
    for (let k = 0; k < 6; k++) { const m = new THREE.Mesh(leafGeo, leafMat); const sc = h * (0.18 + rnd() * 0.1); m.scale.set(sc, sc * 0.8, sc); m.position.set(x + (rnd() - .5) * h * 0.35, Y + h * (0.62 + rnd() * 0.25), z + (rnd() - .5) * h * 0.35); m.castShadow = true; g.add(m); }
  }

  // colinas lejanas con perspectiva aérea
  const segs = 160, ring = new THREE.BufferGeometry(); const P = [], C = [], I = [];
  const near = new THREE.Color('#6f8466'), far = new THREE.Color('#a9b7b4');
  for (let i = 0; i <= segs; i++) {
    const a = i / segs * Math.PI * 2;
    const hgt = 14 + 16 * (0.5 + 0.5 * Math.sin(a * 3 + 1.3)) * (0.6 + 0.4 * Math.sin(a * 7.1)) + 6 * Math.sin(a * 13.7);
    for (const [r, y, col] of [[330, Y - 2, near], [300, Y + hgt, far]]) { P.push(Math.cos(a) * r, y, Math.sin(a) * r); C.push(col.r, col.g, col.b); }
  }
  for (let i = 0; i < segs; i++) { const k = i * 2; I.push(k, k + 2, k + 1, k + 1, k + 2, k + 3); }
  ring.setAttribute('position', new THREE.Float32BufferAttribute(P, 3)); ring.setAttribute('color', new THREE.Float32BufferAttribute(C, 3)); ring.setIndex(I); ring.computeVertexNormals();
  g.add(new THREE.Mesh(ring, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.DoubleSide, fog: false })));

  // volúmenes lejanos genéricos (no son edificios reales del proyecto)
  const vol = new THREE.MeshLambertMaterial({ color: '#d4d6d3' });
  for (const [x, z, w, d, h] of [[-120, 150, 18, 18, 38], [-95, 170, 14, 14, 28], [140, 120, 20, 16, 44], [165, 95, 12, 12, 30], [60, -180, 22, 18, 36], [-150, -120, 16, 16, 26]]) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), vol); m.position.set(x, Y + h / 2, z); g.add(m);
  }

  const fog = new THREE.Fog('#d7dee2', 60, 330);
  return { group: g, fog, sky };
}
