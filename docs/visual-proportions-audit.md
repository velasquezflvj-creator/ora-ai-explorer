# Corrección de proporciones visuales — entrega para auditoría

Base: `fix/compact-responsive-panels`, commit `7e377987956416617d08efb0ea44ee6a01bd229d`.
Rama de corrección: `fix/restore-nicolas-panel-proportions`.
Referencia: repositorio `nossa24/ora-ai-explorer`, commit
`3703753e688d94d68cfeb59fff658044845ca15b` (copia intacta, servida localmente).

## Cambio y causa

La regla responsive de `.tip` fijaba simultáneamente `left: 16px` y `right: 16px`,
anulaba el anclaje y convertía la selección de pisos en una franja hasta 900 px.
`positionTip` además abandonaba el cálculo en esos tamaños.

La tarjeta ahora conserva su ancho intrínseco original en escritorio y mide 244 px
en ventanas de hasta 900 px. Se coloca al lado del piso; si no cabe, se desplaza
por debajo de su anclaje y se limita al espacio entre la cabecera y los controles
inferiores. El punto y la línea conservan la relación visual con el piso.
El redimensionado vuelve a calcular la posición también en móvil.

La ficha interior conserva la geometría original de escritorio y la tarjeta
lateral de 256 px de la rama base en tabletas. En teléfonos, la ficha plegable
queda alineada a la derecha, con ancho máximo de 280 px; el título, espaciado y
control de detalles se ajustan a ese ancho. Los detalles siguen desplazándose
independientemente de los botones de salida y plano.

No cambian datos, configuración de apartamentos, imágenes, videos, prototipo 3D,
trayectorias, duración de animaciones, carga de medios ni navegación del recorrido.
Se conservan las mejoras técnicas de la rama base, incluido autoplay restringido,
cancelación, recuperación, menús y CTA durante el interior.

## Evidencia visual

30 PNGs: Nicolás/corrección × exterior/selección de pisos/interior × cinco tamaños.
Cada pareja tiene viewport exacto, escala de dispositivo 1 y fotograma interior
0,54 s. La prueba guarda `metrics.json` con procedencia y rectángulos medidos.
La galería `index.html` permite abrir cada PNG a tamaño completo.

| Viewport | Tarjeta de pisos Nicolás | Corregida | Ficha interior corregida |
|---|---:|---:|---:|
| 1440 × 900 | 257,47 px | 257,47 px | 280,80 px (original) |
| 1280 × 800 | 257,47 px | 257,47 px | 256 px (original) |
| 900 × 768 | 868 px | 244 px | 256 px |
| 768 × 1024 | 736 px | 244 px | 256 px |
| 390 × 844 | 358 px | 244 px | 280 px, plegada |

La URL pública `https://nossa24.github.io/ora-ai-explorer/` respondió con una
prohibición del proxy (403). Las capturas de referencia corresponden al código
original citado, no a una consulta verificada del despliegue de Pages. En ambos
servidores se bloquea Google Fonts de forma idéntica para evitar comparaciones
entre fuentes distintas; se utilizan las fuentes de respaldo configuradas por
Nicolás. No se afirma equivalencia píxel a píxel con el sitio público con Google
Fonts cargadas. No se publicaron páginas ni se fusionó con main.

## Reproducción

```bash
npm ci
# Usa Chromium del sistema; el runner también admite CHROMIUM_PATH.
npm test
# Clonar la referencia fuera de la aplicación y fijarla al commit citado.
git clone https://github.com/nossa24/ora-ai-explorer.git /tmp/ora-nicolas
git -C /tmp/ora-nicolas checkout 3703753e688d94d68cfeb59fff658044845ca15b
ORA_REFERENCE_DIR=/tmp/ora-nicolas ORA_COMPARISON_DIR=/tmp/ora-comparison \
  node --test tests/visual-reference.test.cjs
node scripts/comparison-gallery.cjs /tmp/ora-comparison
```

La comparación usa puertos 18774/18775 y requiere video HTTP Range real.
La suite habitual usa 18768/18769/18772 y requiere `origin/main` como referencia
histórica de los controles de escritorio, sin cambiar de rama ni fusionar.
La prueba de referencia se omite en `npm test` si no se proporciona
`ORA_REFERENCE_DIR`; debe ejecutarse explícitamente para generar las 30 capturas.

Las regresiones nuevas comprueban límites de las tarjetas para tres planos de
fachada, pisos bajos/intermedios/altos, día/noche y las cinco resoluciones,
además del redimensionado. Las pruebas existentes verifican clics/taps efectivos,
ausencia de controles de salida superpuestos, detalles plegables, foco, ambos
recorridos, habitaciones, errores y restricciones de reproducción. No se probaron
Safari ni dispositivos físicos.

## Resultado de esta ejecución

- Suite completa: 37 pruebas pasaron, 0 fallaron; 1 comparación opcional omitida
  por no proporcionar su checkout de referencia en ese comando.
- Comparación ejecutada por separado con la referencia: 1 prueba pasó, 0 fallaron;
  generó las 30 capturas solicitadas y sus medidas.
- `git diff --check` y comprobación de sintaxis de los scripts: sin errores.
- Revisión visual de los montajes de las cinco resoluciones completada.
- Artefactos de esta sesión: `/workspace/ora-comparison/`, con galería HTML,
  capturas originales, dos montajes de resumen, medidas y logs de las pruebas.
  El ZIP de entrega se genera fuera del repositorio para no incluir 28 MB de PNGs
  en el historial. Los comandos anteriores reproducen las capturas.
