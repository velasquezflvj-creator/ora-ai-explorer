# Créditos y licencias · apartamento 102

El visor del 102 combina recursos propios y de terceros. Todos los de terceros tienen licencias que
permiten el uso comercial; las que lo piden exigen solo atribución, que se da aquí y en el visor.

## Recursos de terceros

| Recurso | Dónde se usa | Autor / fuente | Licencia |
| --- | --- | --- | --- |
| Sofá «GlamVelvetSofa» | Sala | Wayfair LLC, vía [Khronos glTF-Sample-Assets](https://github.com/KhronosGroup/glTF-Sample-Assets) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| Butaca «SheenChair» | Sala y habitación principal | Wayfair LLC, vía Khronos glTF-Sample-Assets | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) |
| HDRI «park» (cielo, terreno lejano y luz del exterior) | Exterior conceptual | [Poly Haven](https://polyhaven.com), selección de [pmndrs/assets](https://github.com/pmndrs/assets) | CC0 1.0 |
| Generador de árboles «ez-tree» (código en `src/vendor/ez-tree/`) | Árboles y arbustos 3D | Daniel Greenheck, [github.com/dgreenheck/ez-tree](https://github.com/dgreenheck/ez-tree) | MIT (ver `src/vendor/ez-tree/LICENSE`) |
| Corteza «Bark013» | Árboles | [ambientCG](https://ambientcg.com), incluida en ez-tree | CC0 1.0 |
| Texturas de hojas (roble, fresno) | Árboles | Repositorio ez-tree | MIT del repositorio; el autor no documenta otro origen |
| three.js r180 | Motor del visor | three.js authors | MIT |

Detalle de los muebles en `modelo/muebles/CREDITOS.md`. Las licencias de terceros excluyen logos y
marcas. El sofá reproduce un producto real de Wayfair (según su ficha en Khronos); se usa como
mobiliario ilustrativo y no implica relación comercial.

## Recursos propios

- **Texturas PBR** (travertino, roble, piso de piedra caliza, laca, yeso, lino, bouclé, tapete, deck y
  el cuadro abstracto): generadas con `tools/texturas_pbr.py` a partir de ruido procedural. No
  provienen de fotografías ni de bibliotecas de terceros.
- **Arquitectura, carpintería, baños, cocina, camas, banquetas, cortinas y accesorios**: modelados por
  código en `tools/generar_glb.py`, `tools/interiores_premium.py` y `tools/mobiliario_premium.py`.
