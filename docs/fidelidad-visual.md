# Fidelidad visual con el original de Nicolás

Esta rama parte de `7a54941` (`fix/compact-responsive-panels`) y toma como referencia el
demo publicado por Nicolás (commit `3703753`, https://nossa24.github.io/ora-ai-explorer/).
No cambia imágenes, videos, medidas comerciales ni el prototipo 3D.

## Qué se recuperó

- **Escritorio (más de 900 px):** selector de pisos y ficha del apartamento idénticos al
  original, en posición, tamaño, tipografía y colores. Las pruebas lo comparan contra
  `3703753` en 1440×900, 1280×800 y 1024×768.
- **Selector de pisos en móvil y tableta:** la misma tarjeta de escritorio, ligeramente
  ceñida (236 px), anclada encima del piso elegido (o debajo, si no cabe) con el punto de
  luz y el trazo que la une al piso. Ya no es una franja fija abajo de borde a borde.
- **Recorrido automático en teléfonos:** solo señala pisos visibles en pantalla.
- **Barra superior:** «Menú» usa la tipografía espaciada de la navegación original; en
  teléfonos es un icono de tres trazos con su nombre para lectores de pantalla. La marca y
  «Tour privado» no se parten en dos líneas.
- **Interior vertical (teléfono y tableta):** el plano y las habitaciones se centran en el
  espacio libre entre la barra y los controles, sin el vacío negro inferior y sin que la
  ficha tape la arquitectura. En tableta vertical, la ficha es una tarjeta de 272 px abajo
  a la derecha.
- **Ficha en teléfonos:** plegada mide unos 125 px; «Detalles» (con flecha) despliega datos
  y habitaciones. Se vuelve a ocultar la descripción larga, como en el original.
- **Pestañas de habitaciones:** las tres caben completas en 320 y 390 px; un rótulo largo
  usa dos líneas en lugar de quedar cortado.
- **Ritmo de entrada:** la ficha vuelve a aparecer al compás del original (≈1,8 s), en vez
  de esperar al final de la animación de las mitades. Sigue sin mostrarse ningún control
  que descarte clics.
- **Aviso de carga:** discreto, solo aparece si la carga tarda más de 0,6 s y se retira con
  el primer cuadro del video, no al final del recorrido.

Se conservan todas las mejoras técnicas aprobadas: recuperación de errores, autoplay
bloqueado, cancelación, carga bajo demanda, menú móvil, clic durante el fundido y «Tour
privado» accesible durante el recorrido.

## Pruebas

```bash
npm test
```

`tests/visual-fidelity.test.cjs` necesita el historial de Git (usa `git archive 3703753`)
y los puertos 18773 y 18774.

## Abrir en un Mac

En el ZIP de prueba, doble clic en «Abrir ORA AI Explorer.command». Si macOS indica que el
archivo es de un desarrollador no identificado: clic derecho → Abrir → Abrir (o
Configuración del Sistema → Privacidad y seguridad → «Abrir igualmente»).
El iniciador sirve los archivos solo para el propio equipo (127.0.0.1) y abre el navegador.
Si el Mac no tiene Python instalado, abre `index.html` directamente.
