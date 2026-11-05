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

## Corrección de proporciones posterior

La tarjeta de pisos permanece anclada y mide 244 px hasta 900 px; ya no se
extiende entre los bordes de la ventana. La ficha plegable de teléfono tiene
ancho máximo de 280 px. Véase [la entrega para auditoría](visual-proportions-audit.md)
para la referencia original, las cinco resoluciones y las capturas reproducibles.
