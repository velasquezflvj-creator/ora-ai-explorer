# Apartamento 102 · Recorrido interactivo V5 (rama `feat/apto-102-recorrido-v5`)

**Propuesta de redistribución conceptual: no es planta verificada ni aprobada.** Se conservan todos los rótulos.
Recorrido 3D libre en tiempo real (sin panorámicas, fotos, videos ni cámaras fijas). V1–V4 no cambian.

```
node server.mjs
http://localhost:8768/apartamento-102/recorrido-v5.html
```
Controles como la V4 (clic captura el ratón, WASD, Mayús, H, Esc). Parámetros de afinado: `?expo=0.45`, `?wb=1.2,1,0.76`,
`?bloom=0.22`, `?densidad=` (fija la densidad), `?calidad=`.

## Estado por fase

| Fase | Estado | Evidencia |
| --- | --- | --- |
| 1. Protección | Hecha: rama nueva desde `b0849cc`; hashes de .blend maestros y GLB registrados y verificados al final; referencia de la V4 a escala Retina | `capturas/recorrido-v5/referencia-v4-retina/` |
| 2. Calidad del visor | Hecha | ver abajo |
| 3. Geometría y materiales (piloto sala/comedor/cocina) | Hecha en alcance piloto | `mediciones/piloto_cambios.json`, `verificacion_glb_v5.json` |
| 4. Iluminación y horneado | Hecha: atlas rehecho con el piloto (4096, 256 muestras, OIDN) | — |
| 5. Gaussian Splatting | Diseñado y planificado (556 vistas); **no ejecutado** (≈ 9–11 h de render en el M2 o GPU en la nube, que requiere autorización) | `docs/gaussian-splatting-piloto.md` |
| 6. Comparación | Hecha para V4 vs V5 (el piloto de splatting no existe aún) | `capturas/recorrido-v5/` |

## Qué se implementó realmente

**Visor (`src/app-recorrido-v5.mjs`)**
- Densidad de píxeles: en Retina parte de 1,5× y se adapta (media 0,85–1,75×, alta 1–2×). La V4 dibujaba a 1× y el
  navegador ampliaba la imagen al doble (medido: 33 % menos nitidez).
- Antialiasing: sin MSAA (caro a densidades altas); SMAA siempre y **TAA de 32 muestras al detenerse** (imagen
  supermuestreada cuando el visitante observa).
- Color: la vista **AgX «Medium High Contrast» de Blender exportada como tabla 3D** (`blender/scripts/exportar_lut_agx.py`),
  con exposición y balance calibrados midiendo el render V3 (luminosidad 0,183 vs 0,159; R/G 1,52 vs 1,53).
- Resplandor sutil solo en fuentes de luz (umbral alto). GTAO solo en «alta» (en «media» la oclusión ya viene horneada).

**Modelo piloto (copia `modelo/web/v5/apto-102-v5.glb`, `blender/scripts/piloto_v5.py`)**
- Biseles de 5 mm en cocina, barra y mobiliario de sala; 3 mm en la puerta de entrada. Los marcos de puerta no se
  biselan (cambiaba su caja 3,3 mm).
- 5 cerámicas procedurales reemplazadas por jarrones CC0 de Poly Haven del mismo alto y posición; utilería CC0 en la
  cocina (tabla de cortar, peras). Todo rotulado «ilustrativo» con su fuente.
- Fusión de vértices + aristas vivas en todas las mallas fijas (misma forma y sombreado): **el atlas pasa de ~12 % a
  ~34 % de aprovechamiento** (≈ 3× resolución efectiva) y los biseles son posibles.
- Verificación: muros, puertas, ventanas, pisos y demás nodos idénticos al original vértice a vértice; solo cambian
  `APA_Cocina` (caja ±0,67 mm), `MOB_Barra` (±0,44 mm), `MOB_Sala` (0 mm) y `ILU_Puerta_entrada` (0 mm), y se añaden
  7 nodos `DEC_*`.

## Mediciones (Mac M2 8 GB, Chromium + Metal, 1440×900 a 2×, caminando; V4 y V5 en la misma corrida)

| | V4 | V5 |
| --- | --- | --- |
| Media | 89–90 fps a 1× | **46–69 fps a 1,6–1,75×** (2,6–3× más píxeles) |
| Alta | 40–53 fps a 1,1–1,25× | **31–33 fps a 1,6×** |
| Carga hasta «listo» | 1,9 s | 2,0 s |
| Memoria JS | 304–322 MB | 342–364 MB |
| Descarga | 37 MB | **58 MB** (atlas HDR 15 MB + GLB con texturas CC0 14 MB) |

Pruebas: `node --test --test-concurrency=1 tests/recorrido-v5-102.test.cjs tests/apartamento-102.test.cjs` → **25/25**.

## Evaluación visual honesta

- **Nitidez:** mejora clara y visible a tamaño real (recortes 1:1 de barra y sala): bordes limpios, sin pixelado en
  lámparas y grifería, texturas definidas. A tamaño reducido la diferencia se aprecia poco.
- **Detalle:** los biseles atrapan la luz en cantos de mesón, fregadero y barra; los jarrones y la utilería CC0 aportan
  materiales reales. Es un piloto: el resto del apartamento conserva la geometría simple.
- **Tono:** más cercano a Blender (medido). Las luminarias y el foseado se ven menos dorados que en la V4 (AgX desatura
  los altos, igual que en el render).
- **No es fotorrealista todavía.** Muros y textiles siguen siendo superficies simples; faltan reflejos con paralaje y
  textiles con caída; el sofá y las butacas de terceros no tienen luz horneada.

## Pendientes y limitaciones

1. Descarga de 58 MB: comprimir atlas y texturas (KTX2) y cargar por espacios.
2. Extender biseles y decoración al resto del apartamento; sustituir textiles (cama, cortinas) por modelos con caída.
3. Reflejos con paralaje (sondas con proyección de caja) y luz horneada para muebles de terceros.
4. Gaussian Splatting: ejecutar el piloto (render + entrenamiento) con autorización de recursos.
5. No probado: Safari, dispositivos físicos, GPU dedicadas.
