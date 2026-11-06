# Apartamento 102 · Recorrido interactivo V2 (rama `feat/apto-102-recorrido-interactivo`)

**Propuesta de redistribución conceptual: no es planta verificada ni aprobada.** El V2 conserva todos los rótulos
del visor original (propuesta, balcón propuesto, alturas provisionales, acabados, muebles y exterior ilustrativos).

## Cómo abrirlo

```bash
cd ora-ai-explorer-feat-apartamento-102-rediseno
node server.mjs
# V2:  http://localhost:8768/apartamento-102/recorrido.html
# V1 (sin cambios, para comparar): http://localhost:8768/apartamento-102/
```

`recorrido.html` también abre con doble clic (file://), como el V1. Parámetros: `?calidad=baja|media|alta`
(fija el perfil), `?exp=0.95` (exposición interior), `?sonda=1.0` (intensidad de las sondas), `?tono=agx`.

En «Caminar» se empieza en la puerta de acceso. Ratón: arrastrar para mirar, clic en el piso para ir.
Teclado: WASD/flechas, **Mayús** para ir más rápido, **H** o **Inicio** vuelve a la entrada. Botón **⌂ Entrada**.
Teléfono y tableta: **mando** (joystick) abajo a la izquierda, arrastrar la escena para mirar, tocar el piso para ir.

## Diagnóstico del proyecto (auditoría)

| Tema | Estado encontrado |
| --- | --- |
| Arquitectura | Sitio estático. Explorador de torres (`index.html`, video) + visores 3D por apartamento (`apartamento-102/`, `apartamento-104/`). Sin framework; `server.mjs` es un servidor estático con Range. |
| Motor | three.js r180 empaquetado con esbuild en un IIFE (`dist/app.js`); datos (GLB, texturas, HDRI) en base64 en `dist/datos.js` para abrir con file://. |
| Modelos | `modelo/apto-102-propuesta.glb` (90 k triángulos, 45 nodos `ARQ_/PRO_/ILU_/APA_/MOB_/PROP_`, 57 materiales sin texturas y `extras` con verificado/categoría/fuente/huella). Muebles de terceros (sofá, butaca) aparte. |
| Materiales | Texturas procedurales propias (1024 px) asignadas en tiempo de ejecución (`pbr102.mjs` + recetas del 104). |
| Navegación | Ya existía y funciona: maqueta (órbita), recorrido de 12 capítulos, caminar con colisiones (muros, ventanas, aparatos, huellas de muebles, hojas de puerta, acceso cerrado), clic para ir, botones táctiles, puntos de información. **No se reconstruyó.** |
| Luz y sombras | Sol con sombras PCF, hemisferio, 4 luces puntuales + 2 de ventana asignadas por cercanía, «habitación neutra» como luz ambiente interior, GTAO solo en alta, espejos reales en baños. |
| Colisiones | 2D en planta (rectángulos + segmentos), validadas por las pruebas del 102. |
| Rendimiento (M2, 1440×900 @2×) | Baja ≈ 70 fps, Media ≈ 35–40 fps, **Alta 5–13 fps**. Sin `?calidad=`, un Mac M2 arrancaba en **Alta** y solo bajaba tras ~120 cuadros lentos. |
| Móvil | Funciona (pruebas responsive); los teléfonos usaban «media». |
| 102 y 104 | El 102 reutiliza `../../apartamento-104/src/acabados.mjs` y `texturas.mjs`. |
| Git | La carpeta **no era un repositorio**. Se creó uno local: rama `base/descarga-original` (estado descargado, sin cambios) y rama de trabajo `feat/apto-102-recorrido-interactivo`. Nada se ha publicado. |
| Defectos encontrados en el V1 | 1) Por la puerta de acceso abierta se ve el cielo y el jardín del HDRI (parece una ventana). 2) El cielo raso no proyecta sombra: el sol entra «por el techo» en baños y hall. 3) Luz interior ≈ 2900 K, dominante ámbar. |

## Qué cambia en el V2

El V1 queda intacto (`index.html`, `src/app.mjs`, `dist/app.js`, `dist/datos.js`, GLB y datos de planta: una prueba lo
verifica contra el commit base). El V2 es una entrada nueva:

| Archivo nuevo | Contenido |
| --- | --- |
| `recorrido.html`, `css/recorrido.css` | Página del V2: perfiles «Móvil/Media/Alta», botón Entrada, joystick. |
| `src/app-recorrido.mjs` | Copia de `src/app.mjs` con los cambios de abajo (marcados con «V2»). |
| `tools/build_recorrido.mjs` | Empaqueta `dist/recorrido-app.js` y `dist/recorrido-datos.js` (no toca `dist/app.js` ni `dist/datos.js`). |
| `tools/medir_rendimiento.mjs`, `tools/capturar_vistas.mjs` | Medición de fps por perfil y capturas comparables, en Chromium con GPU real. |
| `../blender/scripts/*` | Exportación desde Blender (texturas, piso, sondas), importación configurable y cámaras de video. |
| `../tests/recorrido-102.test.cjs` | 5 pruebas del V2. |

Mejoras (por prioridad del encargo):

1. **Luz natural e indirecta: sondas de Cycles.** Diez panoramas 360° (512×256 HDR) renderizados en Blender desde
   cada espacio (sala, cocina, hall, habitaciones, baños, vestier, ropas, balcón), con la gradación del V3
   (+0,8 EV, balance 5000 K). Dentro del apartamento sustituyen a la «habitación neutra»: la luz ambiente y los
   reflejos son los del espacio real renderizado. La sonda cambia al pasar de un espacio a otro.
2. **Temperatura de color:** luces 4200 K (antes ≈ 2900 K), foseado 3500 K y menos intenso; mapeo tonal Neutral con
   exposición calibrada contra el V3 (el AgX de three.js dejaba el interior grisáceo; queda en `?tono=agx`).
3. **Materiales PBR:** texturas fotográficas CC0 a 1024 px (travertino, enchape, roble con el mismo ajuste de color
   del V3 en espacio lineal, relieve de yeso, lino y bouclé) y **piso de 120 × 60 horneado** en Blender: textura
   periódica de 4,8 m donde cada pieza toma un recorte distinto del travertino, juntas de ~2 mm. Relieves reducidos
   para fotos. Pantalla del televisor mate, sin reflejo de espejo.
4. **Sombras y profundidad:** GTAO también en «Media» (ligero, sin MSAA 4×); losa invisible que solo proyecta
   sombra (el sol ya no entra por el techo).
5. **Exterior:** volumen gris neutro detrás de la puerta de acceso (`CTX_corredor_neutro`, rotulado en el código como
   no representativo del corredor real). La vista por las ventanas sigue siendo el exterior conceptual rotulado del V1.
6. **Rendimiento y perfiles:** selección automática por puntero, pantalla y GPU (dedicada → Alta; integrada, p. ej.
   Apple M2 → Media; teléfono/tableta → Móvil). Bajada automática Alta→Media (< 30 fps) y Media→Móvil (< 26 fps)
   dentro del apartamento, salvo que el visitante elija un perfil. Móvil desactiva los espejos reales.
7. **Navegación:** inicio en la entrada, botón y tecla para volver, Mayús para ir rápido, joystick táctil.
   Colisiones, recorrido de 12 capítulos, puntos de información y capas: los del V1, sin cambios.

## Comparación visual

- `capturas/recorrido-v2/comparacion-sala_V3-blender_V2-web_V1-web.jpg`: misma vista de la sala (izquierda Blender
  V3 en Cycles, centro V2 web, derecha V1 web). La cámara del V3 está a 1,45 m y la del visor a 1,60 m, con
  campo de visión similar.
- `capturas/recorrido-v2/comparacion-espacios_V1-izq_V2-der.jpg`: habitación principal, habitación 2, baño
  principal y balcón (V1 izquierda, V2 derecha). `v2-*.jpg`: capturas del V2 a 1920×1080.

Lo que el V2 **no** alcanza respecto al V3 (límites del tiempo real, no promesas pendientes): sombras suaves de área
y luz rebotada exacta (las sondas son una aproximación por espacio, sin paralaje), la línea luminosa del foseado
como fuente de luz, cáusticas del vidrio, y el desenfoque del exterior. El V3 sigue siendo la referencia para
imágenes fijas.

## Pruebas y rendimiento

Ver la sección «Resultados» al final (se completó al cerrar la sesión con los valores medidos).

## Pendientes y recomendaciones

Ver la sección «Limitaciones y siguiente fase» al final.
