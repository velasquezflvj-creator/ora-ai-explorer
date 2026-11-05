# Informe · fase de producción visual del apartamento 102

**Propuesta conceptual, no planta verificada ni modificación arquitectónica aprobada.** Rama
`feat/apartamento-102-rediseno`, PR #4 en borrador. Versión anterior para comparar: commit `ed77ce2`.

## 1. Distribución (congelada antes de la fase visual)

- **Ingreso:** 0,95 m libres entre la despensa (0,40 m) y el mesón norte; 1,00 m medido, limitado por la
  puerta de acceso. Comprobado en planta y con rayos en el modelo 3D (prueba automática).
- **Ropas:** junto al ducto D1, en el antiguo cuarto, con puerta corrediza oculta que se abre al
  acercarse. La columna a la izquierda del acceso se descartó por desagüe (≈3,2 m), ventilación y ruido;
  queda documentada en `capturas/06-comparacion-ubicacion-ropas.png`.
- **Depósito:** no cabe junto con ropas en el mismo cuarto; el almacenamiento está en la despensa.
- **Sin cambios:** dos habitaciones, dos baños, sala con eje libre de 0,85 m al balcón, cocina en U con
  barra-península de dos puestos y balcón. No se agregaron espacios ni se movieron muros para acomodar
  muebles. La habitación 2 sigue siendo dormitorio: el escritorio se cambió por una cómoda baja dentro de
  la misma huella.

## 2. Mejoras visuales

| Área | Antes | Ahora |
| --- | --- | --- |
| Materiales | Texturas procedurales de baja resolución hechas en el navegador | Texturas PBR propias de 1024 px con mapas de color, relieve y rugosidad: travertino en vetas, roble rift, piedra caliza 60 × 120, laca mate, yeso, lino, bouclé, tapete y deck |
| Cocina | Cajas con textura | Roble claro con frentes y juntas reales, mesón de travertino de 4 cm, península con cascada y panel acanalado iluminado, horno, nevera y lavavajillas integrados, grifo de cuello de cisne en latón, repisas con luz, campana integrada, colgantes opalinos y banquetas de bouclé con estructura de varilla |
| Sala | Sofá de terceros, mesa rectangular, TV sobre el muro | Sofá curvo en bouclé crema, mesas redondas de travertino, muro de listones de roble con TV y barra de sonido, cortinas de lino y visillo desde riel empotrado, foseado de luz indirecta, cuadro abstracto propio |
| Baños | Revestimiento hasta 2,10 m, aparatos simples | Travertino a toda altura con juntas, duchas a nivel con rejilla lineal, mampara con perfil y barra negros, brazo de techo, termostática y teleducha, nichos iluminados, muebles suspendidos en laca arena con encimera y poceta, espejos con luz perimetral, sanitarios suspendidos con pulsador negro |
| Ropas | Equipos y gabinete | Carpintería de roble con lavadora-secadora apilada sobre bandeja, lavadero, repisas con cestas y toallas, gabinete alto, rejilla de extracción y registro de mantenimiento hacia el ducto |
| Habitaciones | Cama de bloques | Plataforma flotante de roble, colchón, duvet y pie de cama con caída, almohadas, cabecero de dos paneles tapizados, mesas de noche suspendidas con panel superior y luz, colgantes de lectura, armarios hasta el cielo |
| Corredor | Marcos con molduras | Marcos enrasados, zócalo bajo del color del muro, buñas en el encuentro con el cielo, luz lineal rasante, piso continuo |
| Exterior | Pinos de conos, setos de caja, colinas planas | HDRI fotográfico proyectado sobre el terreno (cielo, horizonte y luz), árboles y arbustos 3D con corteza y hojas, receptor de sombras, baranda de vidrio con perfiles finos, tumbonas de teca y jardinera de gramíneas |
| Luz | Tono ACES, ambiente genérico | Mapeo de tonos Khronos PBR Neutral, rebote cálido del piso, telas con sheen, piedras con brillo muy bajo, oclusión de contacto (calidad alta) sin oscurecer el exterior, escenas de **día y atardecer** |

Comparativas desde las mismas cámaras, con el mismo campo de visión y exposición, en
`capturas/comparativas/`. La diferencia viene de geometría, materiales, iluminación y exterior; no se
cambió contraste ni saturación para "mejorar" las imágenes.

## 3. Experiencia y rendimiento

- Se conservan maqueta, vista cenital, caminata con colisiones, recorrido de 12 capítulos, puntos de
  información, acabados en vivo y capas.
- **Nuevo en Opciones → Capas:** luz **Día / Atardecer** y calidad gráfica **Baja / Media / Alta**. La
  calidad alta baja sola a media si el equipo no sostiene ~28 fps.
- **Carga progresiva:** primero se muestra el apartamento; el cielo HDRI y los árboles se cargan después.
- **Cifras** (sala hacia el balcón, 1280 × 800, medidas con renderizado por software, sin GPU):

| Calidad | Llamadas de dibujo | Triángulos | Texturas en GPU | Árboles / arbustos |
| --- | --- | --- | --- | --- |
| Baja | 94 | ≈183 000 | 48 | 5 / 5 |
| Media | 98 | ≈217 000 | 48 | 9 / 8 |
| Alta | 105 | ≈255 000 | 56 | 13 / 12 |

- **Peso:** `dist/datos.js` ≈15,6 MB (modelo, muebles, texturas y exterior embebidos para que funcione
  sin servidor, también desde el ZIP).

## 4. Licencias

Todo lo de terceros admite uso comercial; el detalle está en [CREDITOS.md](CREDITOS.md): sofá
GlamVelvetSofa (CC BY 4.0) y butaca SheenChair (CC0) de Wayfair vía Khronos; HDRI de Poly Haven (CC0);
ez-tree (MIT) con corteza de ambientCG (CC0). Las texturas de materiales, el cuadro y todo el modelado
son propios.

## 5. Pruebas automatizadas

`npm test` incluye 14 pruebas del 102. Además de programa, envolvente del DWG, colisiones, recorrido y
apertura sin servidor, ahora comprueban:
- el ingreso de 0,90 m o más en planta y medido con rayos en el modelo 3D;
- el paso barra–tabique y el eje mesa–televisor;
- los materiales PBR con mapas de color, relieve y rugosidad, y las telas con material físico;
- la carga del HDRI y de los árboles;
- el cambio día/atardecer y de calidad;
- la puerta oculta de ropas, que se abre al acercarse y se cierra al alejarse.

## 6. Pendientes

Registro separado en [PENDIENTES.md](PENDIENTES.md).
