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

## Resultados de pruebas (ejecutadas el 2026-11-06 en este Mac M2)

| Prueba | Resultado |
| --- | --- |
| `tests/apartamento-102.test.cjs` (V1, antes de cambiar nada) | **14/14** (3 min 14 s) |
| `tests/recorrido-102.test.cjs` (V2, nueva) | **5/5** ejecutada sola (V1 y modelo idénticos al commit base; sondas y texturas; inicio en la entrada, botón Entrada y cambio de sonda; colisiones con todos los muros y el acceso; teléfono: perfil Móvil automático y joystick) |
| `npm test` completo (91 pruebas) | 56 pasan. **33 no se pueden ejecutar en esta copia**: `responsive.test.cjs` y `visual-fidelity.test.cjs` comparan el explorador de torres con `git archive origin/main` y con el commit `3703753` del repositorio original, que esta descarga no trae. Son del explorador, que el V2 no toca. **2 fallaron por saturación** (el V2 corriendo en paralelo con todas las demás y con Blender renderizando); repetidas solas pasan (fila anterior). |
| Compilación | `node apartamento-102/tools/build_recorrido.mjs` sin errores (three 0.180.0, esbuild 0.25.10). |
| Modelos | Los dos visores cargan el GLB, los muebles y las 10 sondas sin errores de consola (pruebas y capturas). |
| Arquitectura | Sin cambios: prueba contra el commit base; en Blender, la huella de vértices y transformaciones de los 74 objetos originales coincide antes y después del V3. |

No verificado aún: Safari (solo se probó Chromium), teléfonos y tabletas físicos (solo emulación de Playwright),
GPU dedicadas (el perfil Alta solo se midió en el M2, donde no corresponde usarlo).

## Rendimiento medido

`tools/medir_rendimiento.mjs`, Chromium con GPU Metal (Apple M2), ventana 1440×900 a 2× (Retina), 5 s girando
caminando en cada espacio. Mediciones consecutivas en las mismas condiciones (la carga de la máquina varía entre
corridas: comparar solo dentro de la misma fila).

| Perfil | V1 caminar (sala / principal) | V2 caminar (sala / principal) | Notas |
| --- | --- | --- | --- |
| Móvil («baja») | 74 / 69 fps | 87 / 83 fps | sin posproceso ni espejos reales |
| Media | 42 / 38 fps | 41 / 50 fps | el V2 añade GTAO y sondas y baja la densidad a 1× |
| Alta | 11 / 5 fps | 11 / 5 fps | GTAO + MSAA 4× a 2×: no apto para el M2; el V2 ya no lo elige solo en GPU integradas |

Carga hasta «listo» (servidor local, sin caché de disco frío): V1 ≈ 0,9–2,5 s, V2 ≈ 1,4–2 s.
Datos: `dist/datos.js` 15,6 MB (V1) → `dist/recorrido-datos.js` 20,5 MB (V2: +4,9 MB de fotos y sondas).
Memoria JS ≈ 100–140 MB. Llamadas de dibujo en el V1, perfil Media caminando: 99–174 por cuadro, 0,2–0,5 M
triángulos (con el compositor activo three.js no informa las llamadas por cuadro).

## Recorrido cinematográfico (Blender)

- `blender/Apartamento_102_Video.blend` (copia del V3; el V3 y el Master no cambian), cámara `CAM_Video` con
  **9 tomas, 53 s a 24 fps (1272 cuadros)**: entrada, cocina, sala y barra, balcón propuesto, habitación 2, baño
  social, habitación principal, baño principal y cierre hacia el balcón. Cada toma une dos nudos consecutivos del
  recorrido del visor (validado para no cruzar muros, muebles ni hojas de puerta); movimiento lento con entrada y
  salida suaves, corte seco entre tomas, marcadores con el nombre de cada toma y el sello de propuesta conceptual.
- En el video la vista directa por las ventanas se desenfoca y sobreexpone: el HDRI de Poly Haven muestra
  edificios que podrían tomarse por el entorno real del proyecto.
- **Estimación medida (2 cuadros de muestra, Cycles 1920×1080, 128 muestras adaptativas + OIDN, M2):
  ≈ 290 s por cuadro → ≈ 103 horas** para el video completo. No se lanzó: el costo es excesivo para el M2.
  Cuadros de muestra en `blender/render/video_muestras/`.
- **Vista previa:** `blender/render/Apartamento_102_Recorrido_previa_640x360.mp4` (H.264, 640×360, 53 s, 12 fps,
  EEVEE con 4 muestras; 13 min de render). Sirve para revisar **movimientos, encuadres y ritmo**, no el color:
  sin sondas de irradiancia horneadas, EEVEE toma casi toda la luz indirecta del cielo y el interior sale frío y
  azulado, y EEVEE avisa que el búfer de sombras (2048) se llena (pueden faltar sombras).
- **Opciones para el render final (medidas en el M2):**

  | Opción | Tiempo por cuadro | Total (1272 cuadros) | Calidad |
  | --- | --- | --- | --- |
  | Cycles 1920×1080, 128 muestras + OIDN | ≈ 290 s | ≈ 103 h | la del V3 |
  | EEVEE 1920×1080, 64 muestras | ≈ 48 s | ≈ 17 h | requiere hornear sondas de irradiancia, subir el búfer de sombras y recalibrar el color antes |
  | Cycles 1280×720, 64 muestras + OIDN (estimado, no medido) | ≈ 65 s | ≈ 23 h | cercana al V3, menos detalle |

  Recomendación: calibrar EEVEE (sondas de irradiancia y de reflexión, búfer de sombras de 4096 MB) y validar
  10 cuadros contra el V3 antes de comprometer ~17 h; o renderizar con Cycles en una GPU dedicada o en la nube.

## Limitaciones y siguiente fase

Pendiente o fuera de alcance en esta fase:
- **Peso de carga:** 20 MB en base64 dentro de un `.js`. Para publicar: texturas KTX2 (Basis), sondas en PNG
  RGBM o KTX2, y carga diferida por espacio en lugar de todo al inicio. Hoy en móvil la descarga es la principal
  barrera.
- **Luz de sondas sin paralaje** (reflejos aproximados en espacios grandes) y sin variante de atardecer (se
  atenúan). Siguiente paso: hornear lightmaps de iluminación indirecta en Blender (requiere un segundo juego de
  UV en el GLB; no se hizo para no regenerar el modelo).
- **Doble mantenimiento:** `src/app-recorrido.mjs` es una copia de `src/app.mjs`. Si el V2 se aprueba, conviene
  convertir sus diferencias en opciones del visor original o reemplazarlo, y mover `VIEWS`, `LIGHTS`, `POIS` y el
  recorrido a un JSON por apartamento (ver `docs/pipeline-apartamentos.md`).
- **Geometría** (necesita autorización): biseles, textiles con caída, decoración, árboles y entorno; la butaca de
  la sala sale verde oscuro en Blender porque el tinte multiplica su textura original verde.
- **Perfil Alta:** no se pudo medir en una GPU dedicada.
- **Pruebas del explorador** que dependen del historial original de GitHub: ejecutarlas en el repositorio real.
