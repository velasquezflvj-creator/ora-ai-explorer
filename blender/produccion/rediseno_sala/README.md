# Rediseño de la sala — sofá escultórico, obra de arte, mueble TV

Composición integral con paleta común (marfil/greige · negro profundo · bronce y pan de oro · roble ahumado). Sustituye
solo mobiliario y decoración; muros, vanos, puertas, ventanas y dimensiones no cambian. El sofá ocupa la huella aprobada
(`propuesta-102.json`, `mobiliario.sofa = [0.15, 1.04, 1.10, 3.16]`).

| Script | Fuente → copia | Estado |
|---|---|---|
| `rediseno_sala_v1.py` | `v4/escena_v4_2_prueba3.blend` → `rediseno_sala/escena_sala_rediseno_v1.blend` | **Ejecutado** (propuesta refinada). Tres vistas previas 1280×720 en `datos/rediseno_sala/previas/`. No aprobado aún como diseño definitivo |
| `rediseno_sala_v2_no_ejecutado.py` | `rediseno_sala/escena_sala_rediseno_v1.blend` → `rediseno_sala/escena_sala_rediseno_v2.blend` | **Preparado, nunca ejecutado** (pausa pedida por el usuario). Requiere revisión (tarea X1 de Codex) antes de usar la GPU |

## v1 (ejecutado)

- **Retira**: sofá `GlamVelvetSofa_*` y `MOB_Sofa`; del mesh `MOB_Sala`, el cuadro anterior (lienzo + marco) y el muro de
  49 listones con respaldo, línea LED y barra de sonido. El TV se conserva.
- **Sofá**: concha continua respaldo-brazos en U (curva con perfil redondeado y afinado hacia el frente), base tapizada sobre
  zócalo de bronce rehundido, asiento continuo, dos cojines de respaldo y tres decorativos con vivo; tapicería bouclé con rizo
  procedural (Voronoi).
- **Obra**: 1,90 × 1,05 m generada proceduralmente (arco negro gestual, pilar, banda y campo de pan de oro, veladura grafito,
  craquelado), relieve por desplazamiento 3 mm, marco de latón satinado con sombra de 12 mm.
- **Mueble TV**: cuatro paneles de roble ahumado de altura completa con juntas de 4 mm; consola suspendida a 24 cm
  (2,04 m × 0,41 m × 0,28 m) en roble ahumado, filete de bronce y tapa de piedra oscura con vetas finas; LED inferior 2700 K.
- Historial de propuestas en la instancia/respaldo: `datos/rediseno_sala/{borrador_1_descartado, borrador_2_descartado,
  propuesta_1, propuesta_2_intermedia, propuesta_2_intermedia_b}/`.

## v2 (preparado, no ejecutado)

- Cojines por **simulación de tela** calibrada en la 4080 (`herramientas/calibrar_tela_cojin.py`): tensión 80 + resortes
  internos 15 conservan el 96 % del volumen con hundimiento natural de 3 cm (sin presión el cojín colapsa; con presión
  sola se infla 30–80 %). Secuencia asiento → respaldos → decorativos con colisiones; vivos extraídos de la costura real.
- Obra 4K con 1 220 trazos de espátula y pincel, relieve real sobre malla de ≈ 1,4 M vértices, marco en L de una pieza con ingletes.
- Mueble TV: cantos 1–1,5 mm con normales endurecidas, piedra apomazada con microrrayado, roble de poro abierto con barniz
  satinado, bronce anisotrópico, LED recalibrado.
- Iluminación: solo se reorientan `Luz_social_1` y `Luz_social_2` hacia el cuadro (potencia y temperatura sin cambio).
- Una sola vista de control 1280×720 (`CAM_control_sala_v2`).

### Opciones (C3)

- **Luz**: por defecto aplica la luz V4.2 definitiva del módulo común `../comun/luz_v42.py` (la misma de C4), además de los
  dos focos reorientados al cuadro. `--luz-prueba3` conserva la luz de la prueba 3.
- **`--sin-render`**: hace todo (simulaciones, obra, mueble TV, luz, cámara de control, copia `.blend`) y se detiene antes del
  render: sirve para probar en CPU sin GPU.
- **`ORA_ESCALA_ARTE=0.5`** (variable de entorno): obra a menor resolución solo para pruebas locales; la ejecución real es 4K.
- La vista de control se renderiza y su exposición se calibra solo en la vista (mediana 0,50–0,55, quemado ≤ 1 %).

### Correcciones previas a la GPU (8 nov 2026, verificadas en CPU contra la escena v1)

La prueba en seco (`herramientas/prueba_seco_sala_v2.py`, en `tests/produccion-blender.test.cjs`) encontró tres fallos en el
borrador original (copia sin corregir en `apartamento-102/capturas/rediseno-sala/borrador_v2_no_ejecutado/`):

1. **Trazos de la obra**: multiplicaba un color RGB (3,) por una textura 2D → `ValueError` de numpy. Habría abortado la
   ejecución en la GPU después de simular los cojines. Corregido.
2. **Vivos de los cojines decorativos**: 0 costuras detectadas (su costura está en el plano medio, no en aristas de caja).
   Ahora se toma el lazo de la banda perimetral más cercano al plano medio, de un solo lado: 264 vértices, tramo máximo 14 mm.
3. **Vivo del asiento**: con umbral de 35° faltaba un tramo de 63 cm del lado largo; con 25° la costura es continua
   (180 vértices, tramo máximo 45 mm).

```bash
$B -b v4/escena_v4_2_prueba3.blend --python rediseno_sala/rediseno_sala_v1.py -- $PWD/rediseno_sala/escena_sala_rediseno_v1.blend $PWD/datos/rediseno_sala/previas
$B -b rediseno_sala/escena_sala_rediseno_v1.blend --python rediseno_sala/rediseno_sala_v2_no_ejecutado.py -- $PWD/rediseno_sala/escena_sala_rediseno_v2.blend $PWD/datos/rediseno_sala/control
```
