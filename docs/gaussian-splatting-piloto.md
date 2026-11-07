# Piloto de Gaussian Splatting · sala, comedor y cocina del apartamento 102

**Estado: diseñado y preparado; no ejecutado.** Propuesta ejecutable para GPU en la nube, con proveedores, presupuesto,
pruebas de aceptación y detención: [gaussian-splatting-nube.md](gaussian-splatting-nube.md). El render de las vistas y el entrenamiento son tareas pesadas que, en
este MacBook Air M2 de 8 GB, no se lanzaron sin autorización (ver «Recursos»). No se contrató ningún servicio.

## Qué es y por qué se evalúa

Un modelo 3D de «gaussianas» (3DGS) se entrena a partir de muchas imágenes con cámara conocida. Si esas imágenes son
renders de Cycles de nuestra escena, el resultado es una representación 3D navegable que reproduce la apariencia de
Cycles (luz global, reflejos, materiales) desde puntos de vista intermedios. Se recorre libremente en el navegador; no es
una panorámica ni un video. La malla del visor actual se conserva (invisible) para colisiones, rótulos y puntos de
información.

## Diseño de cámaras (`blender/scripts/camaras_splat.py`)

- Zona: espacio social (sala, comedor-barra y cocina), solo piso libre (se excluyen huellas de muebles y aparatos de
  `data/propuesta-102.json`, margen 25 cm).
- Rejilla de ~0,45 m × 3 alturas (1,20 / 1,60 / 2,00 m) × 8 direcciones con inclinación variable y desfase angular,
  más vistas cercanas de mesón, barra y sofá. FOV 75°, 1280 × 720, Cycles 64 muestras + reducción de ruido.
- Salida `transforms.json` (formato NeRF/3DGS) compatible con nerfstudio/gsplat, OpenSplat y Brush.
- `--planificar` solo crea las cámaras; `--renderizar` es reanudable y admite tramos (`--desde/--hasta`).

## Herramientas

| Paso | Herramienta | Dónde |
| --- | --- | --- |
| Vistas | Blender Cycles (script anterior) | Mac M2 (horas) o GPU en la nube (minutos) |
| Entrenamiento | gsplat / nerfstudio `splatfacto` (CUDA), OpenSplat (CUDA, CPU o Apple Silicon), Brush (WebGPU) | GPU NVIDIA en la nube recomendada |
| Visor | three.js + Spark o GaussianSplats3D (MIT), sobre la malla actual invisible para colisiones | Navegador |

## Recursos y tiempos estimados (no medidos salvo donde se indica)

- **Render en el M2:** medido en este equipo, Cycles 1920 × 1080 a 128 muestras ≈ 290 s por cuadro. Para 1280 × 720 a
  64 muestras se estima ≈ 60–70 s por vista → **del orden de 6–8 h** para el conjunto planificado (ver número de vistas
  en `blender/splat_sala_cocina/transforms.json`: 556) → ≈ 9–11 h. Con 8 GB de RAM, Blender ocupa ≈ 2–3 GB: viable de noche, sin
  otras tareas.
- **Entrenamiento local (OpenSplat en Apple Silicon):** posible en teoría, pero con 8 GB de memoria unificada habría que
  reducir resolución y número de vistas; tiempo estimado de varias horas y riesgo alto de quedarse sin memoria.
  No recomendado en este equipo.
- **GPU en la nube (recomendado):** una RTX 4090 / L4 / A10 renderiza las vistas con OptiX en ≈ 10–40 min y entrena
  30 000 iteraciones en ≈ 20–40 min. Costo orientativo en proveedores por hora (RunPod, Vast.ai, Lambda): del orden de
  0,4–1,2 USD/h → **un piloto completo cabe en 1–2 h de GPU (≈ 1–3 USD)**. Los precios cambian: hay que confirmarlos
  y requieren tu autorización antes de crear cualquier cuenta o gasto.
- **Descarga en el navegador:** un interior pequeño suele quedar en 0,5–2 millones de gaussianas → 30–120 MB sin
  comprimir (≈ 15–40 MB comprimido, formatos .spz/.ksplat).

## Riesgos conocidos

- La luz y los acabados quedan fijos en el entrenamiento (cambiar acabados u hora del día exige otro modelo).
- Zonas poco vistas (detrás de muebles, bajo la barra) se degradan; se corrige añadiendo vistas.
- Al acercarse mucho a superficies lisas pueden aparecer «manchas» o bordes difusos.
- Fluidez en el M2 y en móviles: depende del número de gaussianas; hay que medirla, no suponerla.

## Siguiente paso propuesto

1. `--planificar` ya se ejecutó: **556 vistas** de 1280 × 720 (rejilla de puntos libres × 3 alturas × 8 direcciones + 4 detalles) → en el M2, ≈ 9–11 h de render; en una GPU en la nube, del orden de 30–60 min.
2. Con autorización: renderizar las vistas en una GPU en la nube (o de noche en el M2) y entrenar con gsplat.
3. Integrar el resultado en una página de prueba junto a la malla de colisiones y medir fps, memoria, descarga y defectos
   desde las mismas cámaras de comparación que la V4/V5.
