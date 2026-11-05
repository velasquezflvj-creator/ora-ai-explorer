# Apartamento 104 · pruebas y rendimiento (fase 3)

## Cómo se probó

- **Pruebas automáticas:** `npm test` (Node + Playwright). Usa Chrome con **render por software (SwiftShader)**, porque el entorno de trabajo no tiene GPU.
- **Inspección visual:** capturas de cada recinto, de las tres propuestas de acabados, de la vista
  técnica, del recorrido y del teléfono. Están en [`capturas/fase3/`](capturas/fase3).

**No se probó** en Safari, en Firefox, en un Mac, iPhone, iPad o Android físicos, ni en ninguna GPU
real. No se afirma compatibilidad con esos entornos.

## Resultado

**`npm test`: 72 pruebas, 72 aprobadas y 0 fallidas** (5 de noviembre de 2026, 10 min 21 s con render por software).
De ellas, 23 son del apartamento 104 (`tests/apartamento-104.test.cjs`); el resto cubre el explorador de torres y la fidelidad visual de las fases anteriores.

| Verificación pedida | Prueba |
| --- | --- |
| Carga del GLB | El visor carga el GLB embebido, dibuja la escena y expone 9 espacios, 13 puntos de información y la leyenda de 4 categorías. También abre desde `file://` |
| Clasificación del modelo | Cada nodo del GLB declara su categoría: verificado, provisional, ilustrativo o propuesta |
| Geometría verificada intacta | La caja de `ARQ_Muros` coincide con la envolvente de 8,10 × 7,60 m. El bloque de código que genera la arquitectura es idéntico al de la fase 2. Los datos del DWG (`geometria-104.json`) y del balcón no cambiaron. La suma 52,62 + 6,81 = 59,43 m² sigue documentada frente a los 60,01 m² rotulados |
| Navegación por todos los recintos | Prueba geométrica sobre una malla de 2 cm, con un cuerpo de 0,44 m de diámetro y todo el mobiliario y las hojas de puerta abiertas. Desde la entrada se llega a la sala, el comedor, la cocina, ropas, la circulación, los dos baños, las tres alcobas (incluido el costado de la cama principal) y el balcón |
| Colisiones con muros y mobiliario | El sofá, la cama, el comedor, la nevera, el mueble de TV y la hoja abierta de la alcoba principal detienen al visitante. Ningún muro es atravesable. Al ocultar el mobiliario, sus obstáculos desaparecen |
| Mobiliario frente a vanos | Ningún mueble ocupa un vano de puerta ni el paso de la puerta-ventana |
| Acceso y regreso del balcón | Se sale por el paso libre de 1,20 m y se vuelve caminando a la sala. Las hojas fijas, la baranda, las sillas y la jardinera son obstáculos. Al desactivar la propuesta vuelven la ventana y el antepecho originales |
| Materiales intercambiables | Las tres propuestas cambian el color de muros, la textura de piso, la cocina, los baños y los textiles. Los cambios por elemento quedan marcados como «Personalizada». El texto «ilustrativos y no contractuales» está visible |
| Puntos interactivos | Los puntos de espacio llevan la cámara al recinto. Los puntos «i» abren su ficha con la categoría, y el de acabados abre la pestaña correspondiente |
| Recorrido completo | Doce capítulos. La trayectoria se muestrea cada 0,04 s, con y sin balcón: no cruza muros, ventanas, muebles, hojas de puerta ni la baranda, y no tiene saltos bruscos. Tocar la escena pausa el recorrido; «Explorar aquí» pasa a caminar en un punto libre; al terminar queda en pausa |
| Tres modos | Maqueta, recorrido y caminar, con transiciones suaves de posición y de campo de visión |
| Vista técnica | «Solo arquitectura verificada» oculta acabados, muebles, balcón y entorno, y muestra en azul los elementos provisionales |
| Adaptación | 390 × 844, 320 × 568, 844 × 390 y 768 × 1024: la ficha, el panel, las pestañas de acabados y la barra del recorrido caben sin desbordar ni tapar los modos |
| Errores | Cada prueba de navegador falla si hay excepciones de JavaScript, errores de consola o recursos que no cargan. Solo se exceptúan las fuentes de Google, que las pruebas bloquean a propósito |
| Calidad alta | La oclusión ambiental (GTAO) arranca y se desactiva sin errores |

Las pruebas de fidelidad visual de la fase 1 (`tests/visual-fidelity.test.cjs`) siguen incluidas en
`npm test`.

## Rendimiento: datos medidos

| Dato | Valor |
| --- | --- |
| Modelo GLB | 2,9 MB, 43 nodos, 53 materiales, 63.442 triángulos |
| `dist/datos.js` (GLB y planta embebidos) | 4,0 MB |
| `dist/app.js` (visor y three.js) | 0,96 MB |
| Llamadas de dibujo por cuadro | 34–87 según la vista |
| Texturas | Generadas en el navegador: 1024 px en escritorio y 512 px en teléfono y tableta |
| Tiempo hasta interactuar (SwiftShader) | 4,9–9,3 s, incluida la generación de texturas |
| Tiempo por cuadro (SwiftShader, 1280 × 800) | Unos 1,3 s en maqueta y unos 5 s dentro del apartamento |

**El render por software no representa una GPU real.** El costo por píxel domina: aun sin luces ni
sombras, un cuadro tarda unos 2,3 s en SwiftShader. Por eso no se reporta un número de cuadros por
segundo para equipos reales: no se pudo medir.

## Medidas para mantener la fluidez

- **Render bajo demanda:** si nada se mueve, la escena no se vuelve a dibujar. Ahorra batería en
  teléfonos.
- **Luces agrupadas:** 4 luces interiores cálidas y 2 luces de ventana se asignan a las fuentes más
  cercanas al visitante, en lugar de 15 luces simultáneas. Así se redujo a la mitad el costo medido.
- **Calidad automática:**
  - En teléfonos y tabletas (puntero táctil o pantalla de menos de 900 px) arranca en calidad media:
    sin oclusión ambiental, sombras de 1024 px, texturas de 512 px y densidad de píxeles limitada.
  - En escritorio arranca en alta.
  - Si dentro del apartamento la calidad alta no sostiene unos 26 cuadros por segundo, baja sola a
    media.
  - Se puede fijar con `?calidad=alta` o `?calidad=media`, o con la opción «Calidad alta» en Capas.
- **Espejos con reflejo real:** solo se calculan dentro del apartamento y cuando están a la vista.
- **Sombras:** una actualización por cuadro, sin repetirla en cada reflejo. El encuadre de la sombra
  del sol sigue al visitante.
- **Entorno exterior:** materiales simplificados (Lambert) e instancias para los 330 pinos.

## Limitaciones conocidas

- **Blender no estaba disponible.** Los muebles se modelan por código (piezas redondeadas,
  superficies de revolución, cortinas plisadas). Tienen buena proporción, pero no el detalle de
  modelos esculpidos.
- **Entorno exterior:** los pinos y arbustos son estilizados. El jardín, la galería de acceso y el
  paisaje son conceptuales y se rotulan así.
- **Luces:**
  - Las luces puntuales no proyectan sombra.
  - La luz de una alcoba puede alcanzar levemente la contigua a través del muro.
  - Solo el sol proyecta sombras.
- **Hojas de puerta:** se muestran siempre abiertas, según el giro interpretado del plano.
- **Primera carga:** en equipos lentos puede tardar varios segundos mientras se generan las
  texturas.
