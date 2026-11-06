# Paneles compactos y navegación responsive

Esta intervención parte de `main` y no incorpora el laboratorio Three.js.
Conserva los recursos audiovisuales, GSAP, configuración comercial, fuentes,
variables de color y las trayectorias/duraciones de las transiciones existentes.

## Comportamiento

- En escritorio amplio, la tarjeta conserva ancho, posición, espaciado,
  tipografía, borde y fondo originales. Las pruebas comparan estas propiedades
  contra una copia exacta de `origin/main` en 1440×900 y 1280×800.
- En ventanas intermedias/tabletas, la ficha mantiene un ancho lateral compacto.
  Si falta altura, solo los detalles se desplazan: las acciones siguen disponibles.
- En pantallas de hasta 600 px de ancho, o de hasta 500 px de alto, la ficha
  comienza plegada. «Ver detalles» despliega información y habitaciones.
  En teléfonos horizontales/ventanas bajas con ancho mayor a 600 px, la ficha
  inferior tiene un ancho máximo de 360 px, en vez de ocupar toda la pantalla.
- El estado inicial plegado se restablece al entrar a otro apartamento y al
  cruzar el breakpoint. El cambio de tamaño sincroniza ARIA, visibilidad y foco.
- «Tour privado» es un enlace independiente de la navegación exterior: sigue
  accesible durante carga, plano y habitaciones. Su texto y destino siguen
  tomando los mismos valores de `js/config.js`; no se configuró un contacto nuevo.
- En el plano se usa la salida de la ficha. El botón flotante no se superpone.
  Durante carga o transiciones de habitación aparece la salida flotante; en una
  habitación permite volver al plano. No se muestran dos controles de regreso.
- La ficha solo se habilita cuando el plano y la transición de entrada están
  listos, evitando mostrar botones que descarten un clic por seguir en estado exterior.

## Pruebas

```bash
npm ci
npm test
```

La suite original comprueba ambos recorridos y recuperación de errores. La suite
`tests/responsive.test.cjs` usa clics/taps visibles, comprueba el destino real de
los eventos, la ficha plegable, giro/redimensionamiento, foco, CTA y cancelación.
La comparación requiere un checkout Git con `origin/main` disponible: el runner
crea una copia temporal mediante `git archive`, sin cambiar la rama de trabajo.
Usa los puertos locales 18769 y 18772; la suite original usa 18768.

Para generar capturas antes/después y medidas:

```bash
ORA_VISUAL_DIR=/tmp/ora-responsive-review node --test tests/responsive.test.cjs
```

Se capturan condiciones de navegador iguales, incluyendo fuentes de respaldo si
Google Fonts no está accesible. Los archivos `before-*`, `after-*` y `metrics.json`
se guardan solo en la ruta indicada, fuera del repositorio. Las capturas fijan
el mismo tiempo de video para comparar la composición. No son nuevas publicaciones.

La verificación automatizada usa Chromium. La revisión final de fuentes y gestos
con Safari y en dispositivos físicos sigue siendo recomendable antes de publicar.

## Visor 3D futuro

Los controles de la ficha se agrupan en `panelDetails`, con acciones de salida
fuera de la región desplazable. Esto permite reutilizar el patrón posteriormente,
pero esta entrega no modifica ni integra el prototipo ni cambia el área de render.

## Corrección posterior a la auditoría del commit 7e37798

- `hideUI` desactiva inmediatamente la interacción y el foco con `inert`, antes
  del fundido. `showUI` los restablece. La salida flotante también queda inerte
  cuando la ficha asume la navegación. El manejador de la salida de la ficha
  comprueba que el plano esté activo y disponible.
- Las transiciones de `.btn` se limitan a fondo, color y borde: no retrasan
  `visibility` ni compiten con la opacidad animada por GSAP. Se conservan las
  duraciones de las animaciones.
- El selector de pisos (`#tip`) conserva sus reglas de escritorio. Hasta 900 px
  usa el ancho de su contenido, limitado a 360 px y al espacio disponible, en
  lugar de estirarse entre ambos bordes. Conserva fuentes, colores y estructura
  originales. Las fichas de acceso al apartamento, el menú y los controles de
  habitaciones mantienen el tratamiento compacto de esta rama.
- La regresión adicional usa 390×844, animaciones normales y un clic físico con
  `page.mouse.click` sobre «Sala y cocina» mientras el panel anterior todavía
  tiene opacidad positiva. No espera a que el botón saliente se oculte. Verifica
  el destino del clic, la habitación final y que el usuario permanezca dentro.
  Antes de corregir la implementación, la comprobación del destino falló.
- La suite suma 33 casos (32 existentes y esta regresión). Las comprobaciones de
  acceso mediante toque también verifican el ancho y los límites del selector
  de pisos; con `ORA_VISUAL_DIR` guardan capturas `floor-selector-*`.

Para la segunda auditoría, repetir el clic rápido en 390×844 y revisar las fichas
plegadas/desplegadas, el selector de pisos y «Tour privado» en 320×568, 390×844,
768×1024, 900×768 y 1440×900. Safari/iPhone requiere validación física adicional.

Resultado de la ejecución completa posterior a la corrección: **33 aprobadas,
0 fallidas, 0 omitidas**, en Chromium (aproximadamente 129 segundos). La evidencia
registró opacidad saliente 0,2153 y recepción correcta del clic por el control de
sala. Recursos audiovisuales, configuración comercial y rama experimental sin
modificaciones. No se realizó fusión ni publicación.
