# Apartamento 104 · Torre 1 · Pinares Ártica Home — medidas verificadas y pendientes

**Identificación confirmada.** En `PLANO_ARQUITECTONICOS_TORRES_PINARES_ARTICA_HOME.dwg`, la lámina
«PLANTA PISO 1 AL PISO 20 · TORRE 1» rotula «APTO 104» y «AREA 60.01m2». Los apartamentos 104 y 105
son los de 60,01 m². Los demás (101–103, 106, 107) rotulan 60,42 m².

El segundo archivo, `modelo_torre_1.dwg`, coincide con esa planta al milímetro tras una traslación
(+1966,834; +1510,522). Las dos fuentes son coherentes.

Lectura: el DWG está en formato AutoCAD 2018 (AC1032) y se convirtió a DXF con LibreDWG.
`tools/extraer_geometria.py` extrae muros (capa MUROS), vanos (VENTANAS y PUERTA), cotas (COTAS),
rótulos y aparatos (MOBILIARIO 1). Las áreas se calculan sobre una malla de 5 mm.

`plano-validacion-104.png` superpone la geometría extraída a las líneas originales del DWG.

> Orientación: «sur» y «este» significan abajo y a la derecha del dibujo. El plano no trae norte
> geográfico; la luz solar del visor es ilustrativa.

## Envolvente

| Medida | Valor | Fuente |
| --- | --- | --- |
| Frente (cara exterior a cara exterior) | 8,10 m | Muro medianero 0,15 + interiores + fachada 0,15 (geometría MUROS) |
| Fondo | 7,60 m | Cota 7,60 (fachada derecha) |
| Fondo interior del muro medianero | 7,45 m | Cota 7,45 |
| Espesor de muros de fachada, medianero e interiores | 0,15 m | Cotas 0,15 |
| Área rotulada en el plano | 60,01 m² | Texto «AREA 60.01m2» |
| Área interior neta (medida) | 52,62 m² | Malla de 5 mm, incluye umbrales |
| Muros dentro de la envolvente | 6,81 m² | Malla de 5 mm |
| Envolvente bruta | 61,56 m² | 8,10 × 7,60 |

El plano no dice cómo se midió el área de 60,01 m². Interior neta más muros da 59,43 m², una
diferencia de 0,58 m² con el rótulo. Lo más probable es que se deba al criterio de medición (por
ejemplo, hasta el eje del muro medianero), pero el plano no lo confirma.

## Espacios (área neta medida)

| Espacio | Área | Medidas en cotas del plano |
| --- | --- | --- |
| Sala · comedor · cocina (abierta) | 18,07 m² | 2,475 de ancho × 7,30 |
| Ropas (abierta a la cocina) | 2,36 m² | 1,21 × 1,95 |
| Circulación | 3,07 m² | 1,28 + vanos 0,80 / 0,85 |
| Baño social | 1,93 m² | 1,21 · 1,39 · 0,72 |
| Alcoba 2 (centro, ventana inferior) | 6,50 m² | 2,50 (1,50 + 1,00 de ventana) × 2,60 |
| Alcoba 3 (esquina inferior derecha) | 8,71 m² | 2,525 (1,00 ventana + 1,525) × 3,60 |
| Alcoba principal (esquina superior derecha) | 8,33 m² | 2,505 (1,24 + 1,265) × 3,55 (fondo derivado de la geometría); ventana lateral 1,00 |
| Baño de alcoba | 2,60 m² | 1,16 × 2,19 |

## Vanos

| Vano | Ancho | Fuente |
| --- | --- | --- |
| Puerta de acceso P2 (desde el corredor, abre hacia la cocina) | 1,00 m | Cota 1,0004 + arco de giro (radio 0,954) |
| Baño social P1 | 0,80 m | Cota 0,80 |
| Alcoba 2 P1 | 0,80 m | Hueco entre muros (cota 1,70 + muro) |
| Alcoba 3 P1 | 0,80 m | Cota 0,80 |
| Alcoba principal P1 | 0,80 m (vano 0,85) | Cota 0,85 |
| Baño de alcoba P1 | 0,80 m | Cota 0,80 |
| Paso sala → circulación (sin hoja) | 0,85 m | Cota 0,85 |
| Ventana sala | 2,475 m | Cota 2,475; marco en VENTANAS |
| Ventana alcoba 2 | 1,00 m | Cota 1,00 |
| Ventana alcoba 3 | 1,00 m | Cota 1,00 |
| Ventana alcoba principal (fachada lateral) | 1,00 m | Marco en VENTANAS |

## Aparatos fijos (posición y huella del plano; forma 3D ilustrativa)

| Aparato | Huella o posición |
| --- | --- |
| Mesón de cocina con lavaplatos y estufa de 4 puestos | 1,475 × 0,50 m, contra el muro del corredor |
| Baño de alcoba | Ducha 1,16 × 0,80; sanitario contra el muro izquierdo; lavamanos junto a la puerta |
| Baño social | Ducha 0,72 × 0,85; sanitario y lavamanos contra el muro superior |

## Propuesta de diseño: balcón de 4,01 m² (no figura en los planos)

Se solicitó el 5 de noviembre de 2026. Ningún apartamento de la Torre 1 tiene balcón ni terraza en
los DWG, así que este balcón es una propuesta, no arquitectura verificada. En el visor aparece
rotulado como «propuesta» y se desactiva con la opción «Balcón de 4,01 m²» o con «Solo arquitectura
verificada». Los datos están en `data/propuesta-balcon.json`.

| Elemento | Propuesta | Relación con el plano |
| --- | --- | --- |
| Ubicación | Fachada inferior, frente a la sala | Usa el vano existente de la ventana de la sala (2,475 m, DWG) |
| Área útil | 4,01 m² (2,475 × 1,62 m) | Exterior a la envolvente: los 60,01 m² y la distribución interior no cambian |
| Losa en voladizo | 2,575 × 1,70 m, 3 cm por debajo del piso interior | Nueva |
| Baranda | 1,05 m, vidrio templado con pasamanos metálico | Nueva |
| Acceso | Puerta-ventana corrediza de dos hojas, 2,10 m de alto, paso libre de 1,20 m | Reemplaza la ventana con antepecho supuesto |

Antes de ofrecerlo en venta requiere:

- diseño estructural del voladizo;
- viabilidad urbanística y modificación de la licencia de construcción;
- aprobación del arquitecto del proyecto (fachada, privacidad con el apartamento 103 y desagüe).

## Interiorismo de presentación (fase 3): qué se apoya en el plano

El mobiliario se ubicó **sin mover ningún muro, vano ni aparato del DWG**. Una prueba automática
verifica que, con todo el mobiliario y las hojas de puerta abiertas, se llega caminando a cada
espacio y al balcón con un cuerpo de 0,44 m de diámetro. También verifica que ningún mueble ocupa un
vano de puerta ni el paso de la puerta-ventana.

| Espacio | Mobiliario ilustrativo | Relación con el plano |
| --- | --- | --- |
| Sala | Sofá de 2,00 m contra el medianero, mesa de centro, mueble de TV flotante de 0,30 m, lámpara de piso y planta | Deja libre el paso de 0,85 m hacia la circulación y el paso de 1,20 m al balcón |
| Comedor | Mesa de 1,20 × 0,80 m con cuatro sillas y lámpara colgante | Quedan 0,62 m libres hacia la cocina por el costado oriental |
| Cocina | Gabinetes superiores, campana, horno, nevera de columna contra el medianero y salpicadero | Mesón, lavaplatos y estufa en la posición del DWG; la nevera queda fuera del giro de la puerta de acceso |
| Ropas | Lavadora, lavadero, gabinete alto y calentador de paso | El DWG no los ubica: se proponen contra el muro norte |
| Alcoba principal | Cama de 1,40 × 1,90 m con cabecero contra el muro oriental, mesas de noche, armario de 1,00 m sobre el muro sur | El armario no tapa la ventana y queda fuera del giro de la puerta. La cama deja 0,64 m entre la hoja abierta y su costado, para llegar al baño |
| Alcoba 3 | Cama de 1,40 × 1,90 m, mesas de noche y armario de 1,40 m sobre el muro norte | El armario queda fuera del giro de la puerta |
| Alcoba 2 | **Propuesta de mobiliario: estudio** con escritorio bajo la ventana, sofá cama y biblioteca | La alcoba y su área (6,50 m²) no cambian; puede amoblarse como alcoba |
| Baños | Mamparas de vidrio, muebles de lavamanos, espejos, revestimiento cerámico hasta 2,10 m | Ducha, sanitario y lavamanos en la posición del DWG |

Las hojas de puerta se dibujan abiertas según el sentido de giro interpretado del plano. Al caminar,
las hojas de las alcobas son obstáculos. Las de los baños abren hacia los aparatos y no se tratan
como obstáculo, para que se pueda entrar.

**Acabados.** Las tres propuestas (Contemporánea cálida, Moderna sofisticada, Minimalista luminosa)
y sus opciones de piso, muros, cocina y baños son ilustrativas. No son especificaciones del proyecto
ni forman parte de ningún ofrecimiento contractual.

**Entorno exterior.** El cielo, el jardín con pinos, las colinas y los volúmenes lejanos son
conceptuales. No representan la vista real del apartamento ni el nivel real del terreno: el jardín
se dibujó 3,20 m por debajo del piso solo para dar profundidad a la vista. El visor lo rotula así
siempre que está visible.

## Pendientes: el DWG no los contiene

| Dato | Qué se necesita | Valor usado solo para visualizar |
| --- | --- | --- |
| Altura libre piso–cielo | Corte arquitectónico o especificación | 2,40 m |
| Espesor de losa y nivel de piso terminado | Corte estructural o arquitectónico | 0,12 m |
| Altura de puertas | Cuadro de carpintería | 2,10 m |
| Antepecho y dintel de ventanas; tipo de ventanería | Fachadas o cuadro de ventanería | 0,90 m y 2,10 m; marco genérico |
| Sentido de giro de las puertas interiores | Hojas con arco en planta | Interpretado de las hojas dibujadas |
| Acabados de pisos, muros, cielos y carpintería | Cuadro de acabados | Paleta ilustrativa |
| Lavadora, lavadero y calentador en zona de ropas | Planta de instalaciones o mobiliario | Lavadora, lavadero y calentador ilustrativos |
| Vista y nivel del terreno | Implantación y fachadas | Entorno conceptual (jardín 3,20 m abajo) |
| Orientación geográfica | Norte en la planta de implantación | Sol ilustrativo |

Todo el mobiliario, los acabados, la carpintería y el entorno exterior son de presentación y no forman
parte del plano. La opción «Solo arquitectura verificada» los oculta, junto con el balcón propuesto, y
muestra en azul los elementos de altura provisional.
