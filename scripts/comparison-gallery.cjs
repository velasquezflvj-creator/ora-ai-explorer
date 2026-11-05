// Render the PNGs produced by tests/visual-reference.test.cjs without resizing them.
const fs=require('node:fs');
const path=require('node:path');
const dir=path.resolve(process.argv[2]||'/tmp/ora-comparison');
const sizes=[[1440,900],[1280,800],[900,768],[768,1024],[390,844]];
let rows='';
for(const [w,h] of sizes)for(const state of ['exterior','pisos','interior']){
 const files=['nicolas','corregido'].map(label=>`${w}x${h}-${state}-${label}.png`);
 for(const file of files)if(!fs.existsSync(path.join(dir,file)))throw Error(`Missing ${file}`);
 rows+=`<section><h2>${w} × ${h} · ${state}</h2><div class="pair">${files.map((file,i)=>`<figure><figcaption>${i?'Corrección':'Nicolás (copia local intacta)'}</figcaption><a href="${file}"><img src="${file}" alt="${state} ${w} × ${h}" loading="lazy"></a></figure>`).join('')}</div></section>`;
}
fs.writeFileSync(path.join(dir,'index.html'),`<!doctype html><html lang="es"><meta charset="utf-8"><title>ORA AI — Comparación visual</title><meta name="viewport" content="width=device-width"><style>body{margin:24px;background:#0b1424;color:#f3eee4;font:14px system-ui}h1{font-size:24px}h2{font-size:18px}.pair{display:flex;gap:16px}figure{margin:0;flex:1;min-width:0}img{width:100%;height:auto}figcaption{margin:10px 0}section{margin:32px 0}a{color:#f2e0b0}</style><h1>ORA AI — Comparación para auditoría</h1><p>Izquierda: código original de Nicolás. Derecha: corrección. PNGs con viewport exacto y escala de dispositivo 1; abre cada imagen para inspeccionar a tamaño completo. Fotograma interior 0,54 s; mismas fuentes de respaldo. La URL pública no pudo consultarse por la política de red.</p><p><a href="metrics.json">Medidas y procedencia</a></p>${rows}</html>`);
console.log('Galería creada:',path.join(dir,'index.html'));
