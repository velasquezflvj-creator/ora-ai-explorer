# Apartamento 102 · Recorrido interactivo V4 (rama `feat/apto-102-recorrido-v4`)

**Propuesta de redistribución conceptual: no es planta verificada ni aprobada.** Se conservan todos los rótulos.
Objetivo de esta fase: mejorar la experiencia de **caminar** dentro del apartamento (recorrido 3D libre en tiempo
real), no producir imágenes. No se usan panorámicas, fotografías, videos ni cámaras fijas.

## Cómo abrirla

```bash
cd ora-ai-explorer-feat-apartamento-102-rediseno
node server.mjs
# V4: http://localhost:8768/apartamento-102/recorrido-v4.html      (V3, V2 y V1 siguen disponibles y sin cambios)
```

**Caminar:** botón «Caminar» (empieza en la puerta de acceso). En computador, **un clic captura el ratón** y la mirada
sigue al ratón; WASD o flechas para moverse (con aceleración y frenado suaves), Mayús para ir más rápido, H o el
botón ⌂ Entrada para volver al inicio, **Esc suelta el ratón** (una segunda Esc vuelve a la maqueta). En teléfono y
tableta: joystick y arrastre para mirar. `?sincaptura` desactiva la captura del ratón (vuelve a arrastrar para mirar).

## Los cinco problemas de mayor impacto al caminar por la V3 (con evidencia)

| # | Problema | Evidencia | Causa | Estado V4 |
| --- | --- | --- | --- | --- |
| 1 | Muros, carpintería, aparatos y mobiliario fijo planos, sin luz rebotada ni oscurecimiento en esquinas y zócalos; los muebles «flotan» | Primeros planos de esquina, zócalo, cabecero y cocina | Solo piso y cielo raso tenían luz horneada; el resto, 4 luces + sonda | **Corregido:** atlas de luz de Cycles para todas las superficies fijas |
| 2 | La luz cambia mientras se camina | Trayecto entrada → habitación: 5 saltos de intensidad (suma de luces 2,4–4,6) por la reasignación de las 4 luces por cercanía | Iluminación interior dinámica por cercanía | **Corregido en superficies fijas:** su luz difusa es la horneada (constante). Las luces dinámicas solo afectan reflejos especulares y muebles de terceros |
| 3 | Rendijas por las que se ve el cielo entre muros y cielo raso | Franja azul en la captura de la cocina | La losa de sombra de la V3 era invisible | **Corregido:** losa visible gris neutra |
| 4 | Controles de visor, no de caminata | Arrastrar para mirar; arranque y frenado instantáneos | Diseño del V1 | **Corregido:** ratón capturado (mirada continua) y velocidad con inercia |
| 5 | Reflejos sin paralaje y aristas perfectamente vivas | Reflejos de sondas fijas por espacio; geometría procedural sin biseles | Sondas sin proyección de caja; GLB sin biseles | **Pendiente** (próxima fase: sondas con proyección de caja; biseles en la copia del modelo) |

## Integración Blender → web (copia del modelo, arquitectura intacta)

`blender/scripts/hornear_lightmaps_web.py` (procesos de Blender en segundo plano; no usa la sesión abierta de Blender,
reservada a las consultas de Codex, y no guarda ningún .blend):

1. **hornear** — abre el V3 en memoria, crea en 29 mallas fijas un segundo juego de UV «luz» (desplegado automático,
   densidad uniforme, empaquetado por forma), hornea con Cycles la irradiancia difusa directa + indirecta en un atlas,
   le quita el ruido con OIDN (nodo Denoise del compositor) y le aplica la gradación del V3.
2. **exportar** — importa el GLB **original** en una escena vacía, le añade solo esas UV y exporta una **copia**:
   `modelo/web/v4/apto-102-v4.glb`. El original no cambia.

`tools/verificar_glb.mjs` compara la copia con el original: **mismos 46 nodos, metadatos, materiales y las 47 165
posiciones de vértice en coordenadas de mundo (tolerancia 0,1 mm)**. Solo se añade TEXCOORD_1.

En el visor (`src/app-recorrido-v4.mjs`, copia de la V3): cada material cuyas mallas tienen todas UV de luz usa el atlas
como única luz difusa (los reflejos de la sonda se conservan, y el color sigue siendo el del acabado elegido). Vidrios,
espejos, emisivos y las carcasas del cielo raso siguen en tiempo real. La variante «sin balcón» (oculta por defecto)
recibe una copia sin hornear del material. El piso y el cielo raso conservan sus horneados planos de la V3.

Ajustes tras revisar las capturas: un 20 % de la luz difusa de la sonda se suma al atlas (evita negros en geometría más
fina que un téxel, como los listones de la barra; `?relleno=`), y las cortinas y las ramas decorativas siguen con luz en
tiempo real (tela fina y plegada).

## Comparación con la V3 (mismas posiciones de cámara)

`capturas/recorrido-v4/antes-despues_V3-izq_V4-der.jpg` (sala, habitación principal, hall, habitación 2, baño
principal) y `v4-*.jpg` a 1920×1080. `primeros-planos-V3-analisis.jpg`: evidencia de los problemas 1 y 3.

Mejoras visibles: degradados de luz en los muros (más claros cerca de ventanas y luminarias, más oscuros en esquinas y
junto al cielo raso), el brillo de las luces de las mesas de noche sobre el cabecero, el foseado iluminando el muro de
listones, sombreado de contacto en carpintería y aparatos, y rendijas cerradas. Sigue sin ser equivalente a Cycles.

## Rendimiento y carga (Mac M2, Chromium con GPU Metal, 1440×900 a 2×, caminando; V3 y V4 en la misma corrida)

| Perfil | V3 | V4 |
| --- | --- | --- |
| Media | 26–33 fps | 43–45 fps |
| Alta | 28–32 fps | 33–34 fps |
| Carga hasta «listo» | 1,2–3,2 s | 3,3–5,5 s |
| Memoria JS | 148–157 MB | 342–364 MB |
| Datos | 23,8 MB | 37,2 MB (+ atlas 8,9 MB y GLB derivado) |

En esta corrida la V3 rindió menos que en su medición de la Fase 3 (47–53 fps en Media): la carga de la máquina varía
entre corridas, por eso solo se comparan valores de la misma corrida (`capturas/recorrido-v4/mediciones/`). Con el atlas
las superficies fijas ya no calculan iluminación difusa dinámica, lo que no empeora los fps. **El costo de la V4 está en
la carga y la memoria**: el atlas es un HDR de 4096 px sin comprimir.

## Pruebas

`node --test --test-concurrency=1 tests/recorrido-v4-102.test.cjs tests/apartamento-102.test.cjs` → **24/24**
(`capturas/recorrido-v4/mediciones/`). Las de la V4 verifican que V1, V2, V3 y el modelo original no cambian, que el GLB
derivado tiene la misma arquitectura, el atlas en muros y superficies fijas, la caminata con inercia y sin atravesar
muros, además de lo heredado (entrada, colisiones, teléfono, horneado, sol, focos, sombras, densidad).
No probado: la captura del ratón en Chrome real (Playwright sin ventana no la permite), Safari, dispositivos físicos.

## Pendiente (siguiente iteración)

1. **Peso:** comprimir el atlas (KTX2/BasisU o RGBM en PNG) y cargarlo por partes; hoy 37 MB y ~350 MB de memoria.
2. **Empaquetado del atlas:** solo ~20 % de la textura se usa; un empaquetado por objeto o por material duplicaría la
   resolución efectiva (detalle de contacto en zócalos y listones).
3. **Reflejos con paralaje:** sondas con proyección de caja por espacio (problema 5).
4. **Atardecer:** el horneado es de día; al atardecer vuelve la luz en tiempo real. Hornear una segunda variante.
5. **Geometría fina:** biseles y textiles en la copia del modelo (requiere autorización; la verificación de arquitectura
   ya existe en `tools/verificar_glb.mjs`).
6. **Muebles de terceros** (sofá, butacas): siguen con luz en tiempo real; hornearles su propio atlas.

## Coordinación con Codex

Todo el trabajo de Blender de esta fase se hizo en **procesos de Blender en segundo plano** sobre el .blend del V3 en
memoria (sin guardarlo; hashes de los maestros verificados antes y después). La sesión de Blender abierta (puerto 9876)
no recibió ningún comando: queda para las consultas de Codex, con sus cambios en memoria sin guardar ni revertir.
