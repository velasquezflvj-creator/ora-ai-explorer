# Apartamento 102 · Recorrido interactivo V3 (rama `feat/apto-102-recorrido-v3`)

**Propuesta de redistribución conceptual: no es planta verificada ni aprobada.** La V3 conserva todos los rótulos
(propuesta, balcón propuesto, alturas provisionales, acabados, muebles y exterior ilustrativos).

## Cómo abrirla

```bash
cd ora-ai-explorer-feat-apartamento-102-rediseno
node server.mjs
# V3: http://localhost:8768/apartamento-102/recorrido-v3.html
# V2 (sin cambios): http://localhost:8768/apartamento-102/recorrido.html
# V1 (sin cambios): http://localhost:8768/apartamento-102/
```

Controles iguales al V2 (Caminar empieza en la entrada; WASD/flechas, Mayús, H o ⌂ Entrada; joystick en teléfono).
Parámetros para afinar sin recompilar: `?calidad=baja|media|alta`, `?densidad=1.25` (fija la densidad de píxeles y
desactiva la resolución dinámica), `?exp=0.9`, `?piso=1` y `?cielo=1` (intensidad de la luz horneada), `?ext=1.6`
(brillo del exterior visto desde dentro), `?calor=1.2`, `?contraste=1.5`, `?vineta=1` (gradación).

## Auditoría: los 10 problemas que más afectaban el realismo (por impacto visual)

| # | Problema | Causa técnica | Archivos responsables | Estado en V3 |
| --- | --- | --- | --- | --- |
| 1 | Piso sin luz real: sin manchas de sol coherentes, sin rebotes, sin sombras suaves ni de contacto bajo los muebles | En tiempo real solo hay sol + 4 luces + sonda por espacio; no hay iluminación global. El GLB no trae un segundo juego de UV para lightmaps | `src/app-recorrido.mjs` (luces, `luzAmbiente`), `tools/generar_glb.py` (sin UV2) | **Corregido en piso:** irradiancia horneada en Cycles con proyección cenital y UV de planta generadas en el visor (`blender/scripts/hornear_planos_web.py`). Sin tocar el GLB |
| 2 | El foseado y las luminarias no iluminan el cielo raso (solo se ve la línea emisiva) | Los emisivos de three.js no emiten luz; el cielo raso no tenía forma de recibirla | `app-recorrido.mjs` (`luz_calida`), GLB `ILU_Cielo_detalles` | **Corregido:** cielo raso horneado (apariencia final de Cycles con el brillo del foseado) |
| 3 | Manchas circulares duras en el cielo raso | Luces puntuales a 2,25 m, a 15 cm del techo | `app-recorrido.mjs` (`poolP`, `LIGHTS`) | **Corregido:** focos dirigidos hacia abajo (4200 K) como los downlights del V3 |
| 4 | Perfil Alta a 5–11 fps en el M2 | Relleno de píxeles: 2× Retina con MSAA 4× en media precisión y GTAO (medido: 1,5× → 26 fps) | `app-recorrido.mjs` (`pixelRatio`, `setupComposer`) | **Corregido:** resolución dinámica por perfil (objetivos 30/45 fps) |
| 5 | Costo y tirones por sombras | El mapa de sombras se recalculaba en cada cuadro, siguiendo a la cámara, con los árboles 3D (19 mallas, 319 000 triángulos) | `app-recorrido.mjs` (`tick`), `entorno102.mjs` | **Corregido:** encuadre fijo de todo el apartamento, 4096/2048/1024 px, recalculado solo cuando algo cambia |
| 6 | Sol del visor distinto al del render: las manchas de luz no coincidían | `SUN_DIR` elegido a mano en el V1 | `app-recorrido.mjs` | **Corregido:** sol de día = sol del HDRI del V3 (33,6°, sur-sureste) |
| 7 | Imagen plana y fría frente al V3 | Neutral sin contraste; sondas con el balance de 5000 K completo | `app-recorrido.mjs` (mapeo tonal), sondas | **Mejorado:** pase de gradación (calidez, contraste, viñeta) calibrado contra el V3. No es AgX exacto |
| 8 | Exterior «de videojuego» visto desde dentro (HDRI nítido, se leen casas) | El cielo proyectado se dibuja igual dentro y fuera | `entorno102.mjs`, `app-recorrido.mjs` | **Corregido:** desde el interior, cielo desenfocado y sobreexpuesto (como la foto de interiores); nítido en el balcón |
| 9 | Muros sin variación de luz (sin rebotes, sin oscurecimiento en esquinas y zócalos más allá del GTAO) | Igual que #1: sin UV2 no hay lightmaps para superficies verticales | GLB (`tools/generar_glb.py`) | **Pendiente:** requiere regenerar el GLB con un segundo juego de UV (cambio de datos, no de geometría): pide autorización |
| 10 | Congelamientos al entrar o cambiar de espacio (0,5–1,8 s) | Compilación de sombreadores, conversión de sondas y del cielo la primera vez que se usan | `app-recorrido.mjs` | **Corregido:** precalentado en momentos ociosos; recorrido de prueba sin pausas (solo durante los primeros segundos de carga) |

Otros puntos pendientes: biseles, textiles con caída y decoración (geometría: requiere autorización); vidrios sin
espesor ni refracción; el atardecer usa luz en tiempo real (el horneado es de día); 23,8 MB de datos sin compresión.

## Qué se implementó (resumen técnico)

- `blender/scripts/hornear_planos_web.py`: abre el V3 sin guardarlo (verificado por hash), pone el piso con un
  albedo constante y lo renderiza con una cámara ortográfica cenital (todo lo demás invisible para la cámara, pero
  proyectando sombras y rebotando luz) → `piso_luz.hdr` = Combined / albedo (irradiancia). El cielo raso se renderiza
  desde abajo → `cielo.hdr`. Ambos con la gradación del V3 (+0,8 EV, 5000 K), 1024×1024, 256 muestras, 6 min.
- `src/app-recorrido-v3.mjs` (copia del V2): genera `uv1` desde las coordenadas de planta de cada malla de piso y de
  cielo; el piso usa la irradiancia horneada como única luz difusa (los reflejos especulares de la sonda se
  conservan; el color sigue siendo el del acabado elegido, así que cambiar acabados sigue funcionando); el cielo
  raso muestra su apariencia horneada. Al atardecer y en la vista técnica vuelve la luz en tiempo real.
- Sol, focos, sombras estáticas, resolución dinámica, gradación, exterior interior y precalentado (ver tabla).
- `tools/build_recorrido_v3.mjs` → `dist/recorrido-v3-app.js` y `dist/recorrido-v3-datos.js`.
- `tools/diagnostico_rendimiento.mjs`: costo de cada componente (sombras, GTAO, densidad, árboles).
- `tests/recorrido-v3-102.test.cjs`: 7 pruebas.

## Rendimiento y carga (medido, Mac M2, Chromium con GPU Metal, 1440×900 a 2× Retina)

`tools/medir_rendimiento.mjs` (5 s girando tras 8 s de calentamiento, en la sala y en la habitación principal, y en el
recorrido automático). V2 y V3 medidos uno tras otro en las mismas condiciones. Datos en `capturas/recorrido-v3/mediciones/`.

| Perfil | V2 caminando | V3 caminando | V3 peor cuadro | Objetivo |
| --- | --- | --- | --- | --- |
| Móvil («baja») | 136–173 fps | 110–155 fps | 31 ms | — |
| Media | 38–44 fps | **47–53 fps** (densidad 1×) | 75 ms | ≥ 45 fps ✓ |
| Alta | 10–13 fps | **34–39 fps** (densidad 1×) | 130 ms | ≥ 30 fps ✓ |

| Carga | V2 | V3 |
| --- | --- | --- |
| Hasta «listo» (servidor local, sin caché) | 0,8–2,0 s | 1,1–1,8 s |
| Datos (`*-datos.js`) | 20,5 MB | 23,8 MB (+3,6 MB de luz horneada) |
| Memoria JS | 109–116 MB | 123–167 MB |

Diagnóstico del costo en Alta (V2): completo 15 fps; sin recalcular sombras 16; sin GTAO 16; árboles sin sombra 16;
**densidad 1,5× en lugar de 2×: 26 fps** → la causa principal era el relleno de píxeles.

Congelamientos: en un recorrido de prueba (entrar, caminar, ir a la habitación principal y al baño) la V3 no tuvo
pausas de más de 150 ms fuera de los primeros 1–2 s de carga. Antes de estabilizar la resolución dinámica había pausas
de 0,7–1 s en cada cambio de densidad; ahora solo cambia tras tres lecturas coincidentes y 15 s de separación, y en
el M2 no llega a cambiar.

Los objetivos se cumplen en esta máquina y ventana; en otras resoluciones o equipos la resolución dinámica ajusta la
densidad (Alta entre 1× y 1,75×; Media entre 0,75× y 1×). No se probó en GPU dedicadas, Safari ni dispositivos físicos.

## Pruebas

`node --test --test-concurrency=1 tests/recorrido-v3-102.test.cjs tests/apartamento-102.test.cjs` → **21/21**
(registro en `capturas/recorrido-v3/mediciones/`). Las de la V3 comprueban que V1, V2 y el modelo no cambian, la luz
horneada (día / atardecer / vista técnica), el sol, los focos, las sombras estáticas, la densidad, la navegación, las
colisiones y el modo teléfono.

## Capturas antes/después (mismas posiciones de cámara)

`capturas/recorrido-v3/`:
- `comparacion-sala_blender-V3_web-V2_web-V3.jpg`: Blender V3 (Cycles) | V2 web | V3 web.
- `antes-despues_V2-izq_V3-der.jpg`: habitación principal, habitación 2, baño principal, hall y balcón.
- `v3-*.jpg` (1920×1080) y `mapas-horneados_piso-izq_cielo-der.png`.

**Evaluación honesta:** la V3 web se acerca al V3 de Blender en tono, calidez y en el foseado iluminado, y las
habitaciones quedan más equilibradas que en el V2. No es equivalente a Cycles: la línea del foseado brilla menos, los
muros no tienen luz rebotada ni sombras de contacto en el zócalo (#9), y la luz no cae hacia el fondo de los
espacios como en el render. No se declara calidad fotorrealista.
