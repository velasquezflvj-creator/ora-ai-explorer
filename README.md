# Ora AI — Explorador de torres

Demo interactivo (réplica del reel de referencia): pasas el cursor por un piso, aparece la tarjeta con el número de piso y la unidad, haces clic y la fachada se abre en esa losa para entrar a la residencia (maqueta 3D → sala → habitación → baño). Los Penthouses (los 2 últimos pisos de cada torre) llevan a su propio recorrido.

## Cómo verlo

```bash
cd ora-ai-explorer
node server.mjs          # → http://localhost:8768
```

Usa el servidor (`server.mjs` atiende peticiones Range, que el video necesita para saltar entre habitaciones). Abrir `index.html` con doble clic no lo he probado.

Parámetros útiles en la URL: `?tod=night` (empieza de noche), `?scan=0` (sin el recorrido automático de pisos), `?debug=1` (dibuja los polígonos de cada piso).

## Estructura

| Ruta | Qué es |
|---|---|
| `img/day.webp`, `img/night.webp` | Tus dos imágenes del edificio, ampliadas 2× (3344×1882) |
| `media/interior-residencia.mp4` | Interior de la residencia (maqueta → sala y cocina → habitación → baño) |
| `media/interior-penthouse.mp4` | Interior del penthouse (maqueta → gran sala → cocina → baño spa) |
| `js/config.js` | **Todo lo editable**: marca, textos, planos de fachada, tiempos del video, link del CTA |
| `js/app.js`, `css/style.css`, `index.html` | Lógica, estilos y estructura |
| `js/vendor/gsap.min.js` | GSAP 3.12.5 (línea de tiempo de la transición), local |

## Cosas que se cambian en `js/config.js`

- **Marca y CTA**: `brand.name`, `brand.tag`, `brand.cta.href` (pon el link de Calendly/WhatsApp; hoy es `#`).
- **Cantidad de pisos y numeración**: `towers.T1/T2` → `floors`, `base`, `pent`.
- **Calibración de pisos**: cada plano de fachada es un cuadrilátero `[arriba-izq, arriba-der, abajo-der, abajo-izq]` en píxeles de la imagen original (1672×941). Abre `?debug=1` para verlos.
- **Datos de la unidad**: `units.res` y `units.pent` (nombre, m², habitaciones, descripción).
- **Tiempos del video**: `plan.hold` (fotograma donde se detiene la maqueta y aparece el panel), `plan.resume`, y `rooms[].hold` (fotograma de cada habitación).

## Reel para redes

`video/ora-ai-reel.mp4`: 1080×1920 (9:16), 37 s, H.264 + AAC, con el mismo formato del reel de referencia (texto arriba y la pantalla de la demo al centro). Se grabó la propia demo cuadro a cuadro a 30 fps.

Música: «Playground Fun» de Ahjay Stelino, de Mixkit (Mixkit Stock Music Free License: uso comercial en video y redes, sin atribución obligatoria). La pista está recortada para que un pulso marcado caiga justo en el clic al piso y está normalizada a -14 LUFS. El archivo de audio suelto no se incluye en el repo.

## Cómo se hizo el video interior

Los dos clips salen del reel de referencia, que estaba grabado con el celular frente a una laptop. Se les corrigió la perspectiva de la pantalla (cámara fija), se recortó el encabezado y la botonera de la web original, se tapó el panel de texto en inglés que venía incrustado en la maqueta (el panel que ves en la demo es HTML en español) y se re-codificó con GOP corto para que los saltos entre habitaciones sean exactos. Son 1600×874, sin audio.

Para reemplazarlos por renders propios del edificio: exporta el mismo recorrido (maqueta → 3 habitaciones), pon los nuevos MP4 en `media/` y ajusta los `hold` de `js/config.js`.


## Desarrollo y pruebas

La aplicación sigue siendo estática: para verla basta con `node server.mjs`.
Node.js 20 o posterior es necesario para las herramientas de prueba.

```bash
npm ci
npx playwright install chromium
npm test
```

En Linux, si faltan bibliotecas del navegador, usa `npx playwright install --with-deps chromium`.
Las pruebas también detectan Chromium en `/usr/bin/chromium`; puedes indicar otro
binario con `CHROMIUM_PATH=/ruta/a/chromium npm test`.
El runner arranca y detiene su propio servidor en el puerto 18768, que debe estar libre.
No hace falta mantener el servidor de desarrollo abierto para ejecutar las pruebas.

La suite comprueba los recursos estáticos, peticiones Range, ambos recorridos y sus
habitaciones, menú móvil, animaciones, recorrido automático y recuperación ante
errores de descarga, cargas pendientes, timeout, búsqueda y reproducción fallida.
También verifica acceso al plano y habitaciones con autoplay bloqueado, indicador
de carga y ocultación/restauración del menú al entrar y salir del apartamento.
Los casos de timeout acortan únicamente el límite de espera de video dentro del navegador
de prueba; el límite real de la aplicación es de 15 segundos por operación.

En móvil, «Menú» permite acceder a Residencias, Penthouses y Amenidades. Se cierra
al seleccionar un modo, tocar fuera o pulsar Escape. `?scan=0` desactiva el recorrido
automático durante toda la sesión, también después de volver del interior.

Los videos se cargan bajo demanda al seleccionar un piso, durante el zoom de entrada.
Si fallan, se recupera la fachada con un aviso; vuelve a seleccionar un piso para
reintentar. El botón de regreso permite cancelar una carga o transición interior pendiente.
Los archivos audiovisuales originales se conservan sin cambios.


### Correcciones de la auditoría del PR #1

Cuando el navegador rechaza `play()` con `NotAllowedError` (restricción de autoplay),
el recorrido continúa mostrando el plano y las habitaciones como cuadros pausados
del mismo video. No requiere habilitar la reproducción automática ni añade recursos.
Los errores reales de descarga o reproducción conservan la recuperación a la fachada.
Durante la carga se muestra «Cargando recorrido…», con opción de regresar a la torre.
El menú principal se oculta y queda fuera del foco durante el recorrido, y se restaura
al terminar la animación de regreso. El CTA del panel y su configuración no cambian.
Las restricciones de autoplay se simulan en las pruebas de escritorio y móvil;
esto no sustituye una comprobación en un dispositivo iOS físico.

## Ficha responsive

Las ventanas intermedias conservan una tarjeta lateral compacta. En teléfonos,
«Ver detalles» abre la información y las habitaciones; la salida permanece visible.
«Tour privado» se mantiene disponible dentro del recorrido. Consulta el
[comportamiento y las pruebas visuales](docs/responsive-panels.md).

## Fidelidad visual con el original

La ficha y el selector de escritorio son idénticos al demo de Nicolás; en móvil y tableta
se usa la misma tarjeta anclada al piso elegido y fichas compactas. Detalles, pruebas y el
iniciador para Mac: [docs/fidelidad-visual.md](docs/fidelidad-visual.md).

## Apartamento 104 en 3D (fase 2)

Primer apartamento real navegable, Torre 1, apto 104, construido desde los planos DWG:
[apartamento-104/](apartamento-104/README.md). Las medidas verificadas y pendientes están en
[apartamento-104/MEDIDAS.md](apartamento-104/MEDIDAS.md).
