# Créditos de los muebles 3D

Los muebles de esta carpeta son modelos de terceros. Se usan como **mobiliario ilustrativo** en el visor
del apartamento 102; no forman parte de la propuesta ni del proyecto.

| Archivo | Modelo original | Autor | Licencia |
| --- | --- | --- | --- |
| `sofa.glb` | GlamVelvetSofa | Wayfair LLC, publicado en Khronos glTF-Sample-Assets | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| `butaca.glb` | SheenChair | Wayfair LLC, publicado en Khronos glTF-Sample-Assets | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) |

Fuente: <https://github.com/KhronosGroup/glTF-Sample-Assets> (carpetas `Models/GlamVelvetSofa` y
`Models/SheenChair`). Las licencias excluyen logos y marcas.

Cambios hechos con `tools/preparar_muebles.py`:
- se fijó una variante de tela y se eliminó la extensión de variantes;
- se quitaron la luz incluida en el sofá y la etiqueta de la butaca;
- se renombraron los materiales y se redujeron las texturas a 1024 px (JPEG).

En el visor, el color de las telas y de la madera se ajusta a la propuesta de acabados elegida.
