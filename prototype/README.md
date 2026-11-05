# ORA AI — Prototipo 3D independiente

**Maqueta sintética provisional. No representa Pinares Ártica Home, no deriva de
sus DWG y no acredita áreas de 54 m² ni 60 m².** Todas las coordenadas, alturas,
puertas y muebles son unidades de escena arbitrarias para probar interacción.
No deben usarse para presupuestos, construcción o comercialización del proyecto.

## Verlo localmente (Mac, Linux)

Requisitos: Node.js 20+ y un navegador con WebGL habilitado.

```bash
npm ci
npm run start:prototype
```

Abrir **http://localhost:8770/prototype/** en el mismo equipo que ejecuta el comando.
El proceso compila Three.js localmente y sirve la aplicación sin CDN ni cargas a
servicios externos. `Control+C` detiene el servidor. El puerto 8770 debe estar libre.
Si el puerto está ocupado:

```bash
npm run build:prototype
PORT=8771 node server.mjs
```

Abrir entonces `/prototype/` en ese puerto. La raíz `/` sigue mostrando el explorador
original; el servidor anterior en 8768 puede seguir funcionando independientemente.
No se requiere GitHub Pages ni un despliegue público.

`prototype/dist/` es generado e ignorado por Git. Después de descargar una rama,
siempre ejecutar el comando de compilación antes de abrir el visor. No usar `file://`.

## Controles

- **Vista general:** arrastrar rota; rueda o pinza controla zoom. Los cuatro puntos
  numerados y los botones de espacios son interactivos. Los puntos también tienen
  geometría 3D seleccionable por raycasting y botones accesibles superpuestos.
- **Explorar:** inicia en un punto seguro de la sala. WASD/flechas desplazan; arrastrar
  sobre la escena cambia la mirada. Los botones de dirección permiten caminar en móvil.
- **Habitaciones:** seleccionan un punto interior seguro, sin alterar el modelo. Son
  saltos de navegación, no una simulación física de traslado entre posiciones.
- **Presentación:** trayectoria de 24 segundos sobre la misma escena. Explorar,
  Vista general o una habitación interrumpen el recorrido. El vuelo introductorio
  es una animación de cámara; las colisiones se aplican al desplazamiento manual.
- **Esc / Restablecer:** regresa a la vista orbital.
- **Acabados:** Roble/Piedra/Arcilla cambian el piso; el selector modifica el color de
  los muros. Los cambios se mantienen entre modos, pero no se guardan al recargar.
- Con movimiento reducido, Presentación conserva una vista fija en lugar de volar.

La navegación usa colisiones horizontales básicas de cámara con muros y muebles,
con margen de separación y subpasos contra el efecto túnel. No incluye gravedad,
escaleras ni simulación de puertas. La maqueta es abierta, sin techo: una vista
expositiva, no un edificio constructivo completo. Los materiales son demostrativos
con iluminación y sombras en tiempo real; no son un catálogo oficial de acabados.

## Código y separación

- `src/model.mjs`: construye la maqueta sintética, obstáculos y posiciones de habitaciones.
- `src/collision.mjs`: resolución horizontal de colisiones, independiente de Three.js.
- `src/app.mjs`: escena, render, modos de cámara, gestos, puntos y materiales.
- `style.css` e `index.html`: interfaz independiente y avisos de provisionalidad.
- `tests/`: pruebas de geometría, interacción real, renderizado y navegación.

El visor no importa `window.ORA`, no cambia los videos y no modifica el código ni
los estilos del explorador de fachadas. Usa Three.js 0.180.0 y esbuild 0.25.10 fijados
en el lockfile. Las texturas de madera son procedurales; no se usan recursos externos.

## Pruebas

```bash
npm run test:prototype
npm test
```

Si no existe navegador instalado: `npx playwright install chromium`.
Se admite `CHROMIUM_PATH=/ruta/al/binario`. El runner del prototipo inicia y detiene
su servidor en 18770; la suite original usa 18768. Ambos puertos deben estar libres.
La prueba WebGL en entornos sin GPU utiliza SwiftShader. Sus resultados no sustituyen
las pruebas de rendimiento en GPU real ni una revisión en Safari/iPhone físico.

La API `window.ORA3D.getSnapshot()` solo expone observación para pruebas. Los tests
cambian modos, habitaciones y materiales mediante controles visibles; también
comprueban selección por raycasting directamente sobre la geometría.

## Sustitución futura por apartamentos validados

1. Identificar de forma inequívoca cada tipología en el CAD y confirmar revisión,
   cuadro de áreas y dimensiones verticales con el arquitecto. La referencia de
   60,01 m² no está certificada como área privada/construida; la de 54 m² sigue pendiente.
2. Modelar cada apartamento por separado, sin deformar uno para obtener el área del otro.
   Validar al menos dos cotas y convertir unidades explícitamente; conservar el origen
   CAD como metadato y usar un origen local para el render.
3. Exportar GLB/glTF 2.0 con mallas y materiales identificables. No incluir en las
   descargas públicas información privada de CAD ni dependencias no autorizadas.
4. Añadir un adaptador GLTFLoader que entregue el mismo conjunto conceptual:
   `group`, obstáculos/colisiones, anclajes de habitaciones, materiales editables y
   puntos seleccionables. El modelo GLB por sí solo no proporciona navegación.
5. Sustituir los límites y colisiones de la maqueta por geometría simplificada o una
   navmesh validada. Las coordenadas y alturas de este prototipo no son reutilizables
   como datos arquitectónicos.
6. Recalibrar cámaras, puntos de mirada y velocidad; no conservar una trayectoria
   que atraviese arquitectura real. Mantener solo un controlador de cámara activo.
7. Aplicar materiales oficiales y optimizar texturas/luces; fijar presupuestos de
   memoria y tiempos de carga con pruebas en computadores y móviles reales.
8. Integrar mediante un tipo de recorrido por unidad (`video` o `gltf`) en una entrega
   posterior. Mantener fachadas y videos existentes como referencia/alternativa;
   esta prueba de concepto no cambia su comportamiento ni sus destinos comerciales.

No se han creado modelos reales de 54/60 m² en esta entrega ni se ha publicado el sitio.
