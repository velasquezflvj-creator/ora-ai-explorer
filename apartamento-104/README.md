# Apartamento 104 · Torre 1 en 3D

Experiencia 3D navegable del apartamento 104 de Pinares Ártica Home (60,01 m² rotulados), construida
sobre la planta del DWG arquitectónico entregado. Toda la experiencia ocurre sobre un mismo modelo:
maqueta, recorrido, caminata, acabados y balcón propuesto.

- **Abrir:** `index.html` funciona con doble clic y desde un servidor local. En un Mac, usa
  `mac/Abrir Apartamento 104 en 3D.command`.
- **Modos:**
  - **Maqueta:** vista orbital y cenital con zoom. Se elige un espacio con su punto o desde la lista.
  - **Recorrido:** presentación cinematográfica en 12 capítulos, de unos 2 minutos 20 segundos:
    1. Vista general
    2. Acceso
    3. Entrada
    4. Sala y comedor
    5. Cocina y ropas
    6. Alcoba principal
    7. Baño principal
    8. Alcoba 3
    9. Alcoba 2 (estudio)
    10. Baño auxiliar
    11. Regreso a la zona social
    12. Balcón y vista exterior

    Tocar la escena o pulsar la barra espaciadora pausa el recorrido. «Explorar aquí» pasa a caminar
    desde ese punto. La barra de avance permite saltar a cualquier momento.
  - **Caminar:** primera persona a 1,60 m. Colisiona con muros, ventanas, aparatos, mobiliario
    visible y hojas de puerta abiertas. Se mueve con WASD o flechas, tocando el piso, o con los
    botones táctiles.
- **Puntos interactivos:**
  - Un punto por espacio, que lleva la cámara hasta él.
  - Trece puntos de información («i»). Cada uno dice si el elemento está verificado en el DWG, es
    una medida provisional, es ilustrativo o es una propuesta.
- **Acabados ilustrativos (no contractuales):**
  - Tres propuestas: Contemporánea cálida, Moderna sofisticada y Minimalista luminosa.
  - Además se pueden elegir por separado el piso (5 opciones), los muros (6), la cocina (3) y los
    baños (3).
  - Cambian en vivo, sin recargar.
- **Capas:**
  - Balcón propuesto.
  - Mobiliario.
  - Cotas del plano.
  - «Solo arquitectura verificada»: vista técnica sin acabados, muebles, balcón ni entorno, con los
    elementos provisionales en azul.
  - Calidad alta: oclusión ambiental.
- **Propuesta:** balcón de 4,01 m² en la fachada de la sala. No figura en los DWG. Se puede activar
  o desactivar, y está documentado en
  [MEDIDAS.md](MEDIDAS.md#propuesta-de-diseño-balcón-de-401-m²-no-figura-en-los-planos).

## Cuatro categorías

| Categoría | Qué incluye | Cómo se ve |
| --- | --- | --- |
| Verificado en DWG | Muros, vanos, pisos de cada espacio, posición y huella de mesón, lavaplatos, estufa, duchas, sanitarios y lavamanos | Nodos `ARQ_Muros`, `ARQ_Piso_*` y `APA_*`, con `categoria: verificado` |
| Provisional | Altura libre de 2,40 m, losa, dinteles, antepechos y cielo raso | En la vista técnica, en azul. Nodos `ARQ_Losa`, `ARQ_Dinteles_Antepechos` y `ARQ_Cielo` |
| Ilustrativo | Mobiliario, acabados, carpintería, revestimientos, luminarias y entorno exterior | Nodos `MOB_*` e `ILU_*`. El entorno se rotula «conceptual» |
| Propuesta | Balcón de 4,01 m², puerta-ventana corrediza y su mobiliario | Nodos `PROP_*` y `MOB_Balcon`, rotulados «propuesta» |

La alcoba 2 se presenta amoblada como estudio. Es una **propuesta de mobiliario**: la alcoba, su
área (6,50 m²) y su puerta no cambian.

Detalle completo de medidas y decisiones de interiorismo: [MEDIDAS.md](MEDIDAS.md).
Pruebas y rendimiento: [PRUEBAS.md](PRUEBAS.md).

## Estructura

| Archivo | Contenido |
| --- | --- |
| `tools/extraer_geometria.py` | DXF → `data/geometria-104.json` (muros, vanos, cotas, espacios, aparatos) |
| `tools/generar_glb.py` | Geometría → `modelo/apto-104.glb`, con arquitectura, aparatos, mobiliario, acabados y propuesta |
| `src/app.mjs` | Visor: modos, recorrido, colisiones, capas, puntos de información y vista técnica |
| `src/texturas.mjs` | Texturas procedurales (color, normal map y rugosidad), periódicas y sin descargas |
| `src/acabados.mjs` | Catálogo de acabados y las tres propuestas |
| `src/entorno.mjs` | Entorno exterior conceptual: cielo físico, jardín, pinos y colinas |

## Regenerar

```bash
dwg2dxf -y -o planos.dxf PLANO_ARQUITECTONICOS_TORRES_PINARES_ARTICA_HOME.dwg   # LibreDWG
python3 tools/extraer_geometria.py planos.dxf "" data/geometria-104.json          # requiere ezdxf
python3 tools/plano_validacion.py data/geometria-104.json plano-validacion-104.png
python3 tools/generar_glb.py data/geometria-104.json modelo/apto-104.glb data/propuesta-balcon.json
npm i --no-save three@0.180.0 && node tools/build.mjs                            # requiere esbuild
```

Los DWG no se incluyen en el repositorio porque el repositorio es público.

**Blender no estaba disponible** en el entorno de trabajo. Por eso `modelo/apto-104.glb` se escribe
directamente desde Python (glTF 2.0): las piezas redondeadas, las superficies de revolución y las
cortinas se generan por código. Se puede abrir y refinar en Blender, porque los nombres de nodos y
materiales son estables. Las texturas se generan en el navegador para no depender de descargas ni de
licencias de terceros.
