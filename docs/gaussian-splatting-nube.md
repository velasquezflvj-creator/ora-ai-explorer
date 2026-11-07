# Piloto de Gaussian Splatting en GPU de la nube · propuesta ejecutable y presupuesto

**Apartamento 102 · sala, comedor y cocina. Propuesta de redistribución conceptual: no es planta verificada ni aprobada.**
Estado: **todo preparado y probado en el Mac; nada contratado ni ejecutado en la nube.** Requiere tu autorización
(crear la cuenta y cargar el saldo los haces tú; ver «Qué necesito de ti»).

Objetivo: comprobar si un splat entrenado con renders de Cycles mejora **sustancialmente** el fotorrealismo de la V5
al caminar, manteniendo three.js (V5) para colisiones, navegación y rótulos.

---

## 1. Proveedores comparados (precios consultados el 7-nov-2026)

| | **RunPod · Secure Cloud** (recomendado) | RunPod · Community Cloud | **Vast.ai** (alternativa) |
|---|---|---|---|
| RTX 4090, por hora | **0,89 USD** | 0,34 USD | mín. 0,37 · mediana **0,51 USD** (40 ofertas verificadas, fiabilidad ≥ 98 %) |
| Equivalentes | L40S 1,09 · RTX 5090 1,19 | L40S 0,79 · RTX 5090 0,69 | según mercado |
| Disco | 0,10 USD/GB-mes en uso; 0,20 detenido | igual | ≈ 0,20 USD/GB-mes (varía por anfitrión) |
| Transferencia | sin cargo publicado | sin cargo publicado | 2,7–29 USD/TB según anfitrión → < 0,01 USD aquí (≈ 0,1 GB subida + 0,3 GB bajada) |
| Facturación | prepago, por segundo | prepago, por segundo | prepago, por segundo |
| Dónde corre | centros de datos certificados | equipos de terceros | equipos de terceros (filtrar «verified») |
| Auto-detención desde dentro | `runpodctl pod stop $RUNPOD_POD_ID` (clave limitada ya inyectada) | igual | `vastai stop instance $CONTAINER_ID` (clave por instancia `CONTAINER_API_KEY`) |

Fuentes: [RunPod pricing](https://www.runpod.io/pricing) (actualizado el 4-nov-2026),
[RunPod: gestionar pods](https://docs.runpod.io/pods/manage-pods.md), API pública de ofertas de Vast.ai
(`console.vast.ai/api/v0/bundles`, consulta guardada en la medición), [Vast.ai: variables del contenedor](https://docs.vast.ai/guides/instances/docker-environment).
Los precios de Vast.ai cambian minuto a minuto; los de RunPod, por publicación. **Se vuelven a confirmar en el panel antes de crear la máquina.**

**Recomendación: RunPod Secure Cloud con RTX 4090.** Cuesta más que Community o Vast, pero el modelo del apartamento
queda en un centro de datos certificado y no en el equipo de un particular, y la diferencia total es de 1–2 USD.
Si prefieres el mínimo costo, Vast.ai «verified» con la misma receta (los scripts detectan el proveedor solos).

## 2. Compatibilidad verificada

| Pieza | Versión fijada | Qué se verificó y dónde |
|---|---|---|
| Blender | **5.2.3 LTS** (la misma del Mac) | Linux x64 publicado; SHA-256 oficial fijado en `instalar.sh` (`78486c01…`). La escena se abrió y renderizó **desde la copia empaquetada** en el Mac (12 vistas, 0 texturas faltantes). OptiX se comprueba al instalar |
| GPU / CUDA | RTX 4090 (Ada, sm 8.9), controlador ≥ 550, imagen CUDA 12.4 «devel» (Ubuntu 22.04) | `instalar.sh` aborta si el controlador es menor |
| Entrenamiento | **gsplat 1.5.3** + su entrenador de referencia (etiqueta v1.5.3), torch 2.4.1+cu124, Python 3.10 | Las ruedas oficiales de gsplat 1.5.3 **solo existen para Python 3.10 / torch 2.4**: por eso esa combinación exacta. Revisé el código del entrenador: lee COLMAP **binario** (su lector de texto no funciona en Python 3, se evitó) y normaliza el mundo por defecto (se desactiva para que el splat quede en metros) |
| Poses de cámara | `nube/splat/a_colmap.py` | **Verificado en el Mac:** proyecta igual que la cámara de Blender con un error máximo de **0,0015 px** (556 vistas de entrenamiento, 10 de control) |
| Visor | **Spark 2.4.0** (MIT, World Labs) para three ≥ 0.180 — el proyecto usa r180 | **Verificado en el Mac:** se empaqueta con la V5 en un solo archivo (una copia de three), sin modificar la V5; orientación Blender→three correcta; parche de calibración centrado (alineación exacta con la malla); color sRGB fiel (esperado 200/100/50, medido 192/97/50); colisiones de la V5 activas; tecla M alterna splat/malla |
| Compresión | SPZ con el propio Spark (`tools/splat/a_spz.mjs`) | Sintético de 1,5 M: 84 MB → **11,5 MB**, carga en 2,4 s |

Lo que **solo** se puede verificar en la nube (y es lo primero que se hace, en una prueba de humo de ≈ 5 min que
cuesta centavos): que OptiX renderiza la copia, que gsplat compila y entrena, y las métricas.

## 3. Traslado de archivos sin tocar los maestros

1. `zsh tools/splat/preparar_paquete.sh` (en el Mac, ≈ 15 s): Blender abre el `.blend` V3 **en segundo plano y en
   solo lectura**, aplica el piloto V5 (biseles y decoración CC0), empaqueta texturas y modelos y **guarda una copia**
   en `../ora-splat-paquete/` (fuera del repositorio). Compara el SHA-256 de los 3 `.blend` maestros y del GLB original
   antes y después y **falla si alguno cambió** (ejecutado 4 veces: siempre intactos).
2. Paquete: `ora-splat-paquete.tar.gz` (**96 MB**) con la escena autónoma (80 MB), la nube de puntos inicial
   (250 000 puntos de las superficies reales), los scripts, la configuración, las 10 capturas de referencia de la V5 y
   `MANIFIESTO.sha256` (hash de cada archivo). Su propio hash queda en `ora-splat-paquete.tar.gz.sha256`.
3. Subida: `scp -P <puerto> ora-splat-paquete.tar.gz root@<ip>:/workspace/` (datos de conexión del panel).
   En la nube, la etapa `verificar` comprueba el manifiesto antes de empezar.
4. Bajada: `scp … /workspace/paquete/resultados/ora-splat-resultados.tar.gz .` y comparar con su `.sha256`.
   Contiene el splat (`.ply`), las métricas, las hojas Cycles | V5 | splat y los registros (≈ 300 MB).
5. Al terminar: **eliminar** la máquina (no solo detenerla) para borrar la copia de la escena del proveedor.

Los maestros **nunca salen del Mac**: lo que viaja es una copia.

## 4. Procedimiento de ejecución (RunPod Secure Cloud)

1. **Tú:** crear la cuenta en runpod.io, cargar **10 USD** de saldo prepagado (es el tope físico del gasto) y añadir
   tu clave SSH pública. No me compartas contraseñas ni claves.
2. Crear un Pod: GPU **RTX 4090 ×1**, plantilla oficial **«RunPod PyTorch» con CUDA 12.4** (Ubuntu 22.04),
   disco del contenedor **40 GB**, sin volumen de red. Confirmar el precio por hora en pantalla.
3. Subir y lanzar (desde el Mac; ≈ 1 min):
   ```bash
   scp -P <puerto> ../ora-splat-paquete/ora-splat-paquete.tar.gz root@<ip>:/workspace/
   ssh -p <puerto> root@<ip> 'cd /workspace && tar xzf ora-splat-paquete.tar.gz && cd paquete && TARIFA_USD_H=0.89 LIMITE_H=4 nohup bash nube/splat/ejecutar.sh > /dev/null 2>&1 &'
   ```
4. Etapas automáticas (registro en `registro/ejecutar.log`; costo acumulado en `registro/estado.txt`):
   `verificar → instalar → humo → render → colmap → entrenar → metricas → empacar`. Si una falla, se corrige y se
   reanuda desde ella (`bash nube/splat/ejecutar.sh <etapa>`): lo hecho no se repite.
5. Bajar los resultados apenas aparezca `registro/LISTO`. Hay 45 min de gracia; luego la máquina se detiene sola.
6. **Eliminar el Pod** en el panel (o `runpodctl pod delete <id>`). Revisar en *Billing* que el gasto coincide con el
   costo registrado.
7. En el Mac: `node tools/splat/a_spz.mjs splat_sala_cocina.ply apartamento-102/modelo/web/splat/splat_sala_cocina.spz`
   y abrir `http://localhost:8768/apartamento-102/recorrido-splat.html?splat=modelo/web/splat/splat_sala_cocina.spz`.

Vast.ai: igual, eligiendo una oferta RTX 4090 «verified», fiabilidad ≥ 98 %, CUDA ≥ 12.4, imagen
`nvidia/cuda:12.4.1-devel-ubuntu22.04`, 40 GB, acceso SSH; `TARIFA_USD_H` = precio mostrado.

## 5. Pruebas que demuestran si el piloto supera a la V5

**Vistas de control** (10, `apto-102.json → splat.control`): poses a 1,6 m dentro de sala, barra, cocina y entrada,
**nunca usadas para entrenar**. Cycles las renderiza a 128 muestras (la «verdad»); la V5 ya está capturada desde las
mismas poses (error de pose 0 mm / 0°, FOV 75°, 1280×720) y el splat se renderiza en la nube desde ellas.

**A. Fidelidad visual frente a Cycles** (`metricas.py`; LPIPS es la métrica más cercana a la percepción humana):

| Criterio de éxito | Línea base V5 |
|---|---|
| LPIPS medio del splat **≥ 30 % menor** que el de la V5 | se mide en la nube |
| El splat gana en LPIPS en **≥ 8 de 10** vistas | — |
| PSNR medio del splat **≥ V5 + 4 dB** | **21,1 dB** (preliminar, frente a Cycles de 16 muestras en el M2) |
| Revisión visual de las 10 hojas Cycles · V5 · splat: sin manchas ni flotantes en zonas de paso | tú decides |

**B. Rendimiento en el MacBook Air M2** (`medir_splat.mjs`: V5 y splat en la misma corrida, 1440×900, caminando y girando):

| Criterio de éxito | Medido hoy con splats sintéticos |
|---|---|
| **≥ 45 fps** de mediana (objetivo de Media), percentil 95 ≤ 40 ms | 0,8 M: 50 fps · 1,5 M: 37–45 fps (densidad 1,0 / 0,75) |
| **≥ 30 fps** en el peor caso de giro (objetivo de Alta) | 1,5 M a densidad Retina: **20 fps** ✗ → por eso se usa densidad 1,0 |
| Carga ≤ 6 s; descarga del splat ≤ 60 MB (SPZ); memoria JS ≤ 700 MB | 1,5 M SPZ: 2,4 s, 11,5 MB, 410 MB |

Consecuencia ya aplicada: el entrenamiento usa la estrategia **MCMC con tope de 1 000 000 gaussianas** y el piloto
arranca a densidad 1,0. Un splat real tiene gaussianas de tamaños variados (más sobredibujo que el sintético): el
resultado puede quedar por debajo y entonces se prueba con 0,6 M (`MAX_GAUSS=600000`, solo reentrenar: ≈ 0,4 USD).

**C. Integridad** (`tests/recorrido-splat-102.test.cjs`, 4 pruebas, todas pasan): V4, V5, GLB original y `.blend`
maestros sin cambios; poses exactas; carga, orientación, alineación y color del splat; alternancia con la malla y
colisiones activas. Más las 25 pruebas de la V5 y del V1 (25/25).

**Veredicto:** el piloto «supera a la V5» solo si cumple A **y** B. Si cumple A pero no B, la conclusión es que el
splat sirve para puntos de vista destacados o equipos más potentes, no para caminar en el M2.

## 6. Presupuesto y detención

| Etapa | Tiempo estimado en RTX 4090 | Base |
|---|---|---|
| Instalación | 10–15 min | descarga de Blender (385 MB) y torch, compilación de 2 extensiones |
| Prueba de humo | ≈ 5 min | 4 vistas + 300 pasos |
| Render (556 + 10 vistas, 128 muestras, OptiX) | 30–50 min | medido en el M2: 18 s/vista a 16 muestras; la 4090 es ≈ 20–30× más rápida en Cycles. **Se mide tras 12 vistas y aborta si la proyección supera la mitad del límite** |
| Entrenamiento (30 000 pasos, ≤ 1 M gaussianas) | 25–40 min | referencia de gsplat en escenas de tamaño similar |
| Métricas y empaque | ≈ 5 min | |
| Gracia para descargar | ≤ 45 min | la máquina se detiene sola |
| **Total** | **≈ 1,5–2,5 h** | |

| Escenario (RunPod Secure 0,89 USD/h) | Costo |
|---|---|
| Esperado (2,5 h) + disco 40 GB un día | **≈ 2,4 USD** |
| Tope del guardián (4 h) | **3,6 USD** |
| **Presupuesto máximo autorizable** | **10 USD** (saldo prepagado: el proveedor no puede cobrar más) |

Con Vast.ai a la mediana (0,51 USD/h): esperado ≈ 1,3 USD; tope 2,1 USD.

**Detención garantizada** (`nube/splat/guardian.sh`, arranca solo en la primera etapa); detiene la máquina con lo que ocurra primero:
1. **Límite duro de 4 h** desde el arranque (`LIMITE_H`); `ejecutar.sh` se niega a empezar si `LIMITE_H × tarifa` supera el presupuesto.
2. Trabajo terminado + 45 min de gracia.
3. GPU inactiva 20 min sin ninguna etapa en marcha (p. ej., si algo falla de noche).
4. Además: saldo prepagado de 10 USD como tope físico, y la eliminación manual del Pod al final (paso 6).

**Gasto verificable:** `registro/estado.txt` (tiempo × tarifa, minuto a minuto), `registro/guardian.log` (hora y motivo
de la detención), `render_log.csv` (segundos por vista) y el historial de facturación del proveedor; los cuatro
deben coincidir.

## 7. Riesgos y qué pasa si ocurren

| Riesgo | Mitigación |
|---|---|
| Algo no instala o no entrena | La prueba de humo lo detecta en ≈ 20 min (≈ 0,3 USD) y se detiene |
| Render más lento de lo estimado | Se proyecta tras 12 vistas; si no cabe, aborta (o se baja a 64 muestras) |
| Splat con manchas en zonas poco vistas | Las vistas de control y las hojas lo muestran; se añaden cámaras y se reentrena (≈ 1 USD) |
| El M2 no sostiene los fps | Tope de gaussianas; segunda variante de 0,6 M sin volver a renderizar |
| Luz y acabados fijos | Limitación conocida: cambiar acabado u hora exige otro splat. La V5 sigue siendo la base configurable |
| Descarga pesada | SPZ con Spark (≈ 7× menor); armónicos de grado 1 si hiciera falta |

## 8. Qué necesito de ti

1. Autorización para gastar **hasta 10 USD** y la elección de proveedor (recomiendo RunPod Secure Cloud).
2. Que crees la cuenta, cargues el saldo y añadas tu clave SSH; después me pasas la **IP y el puerto** del Pod
   (no contraseñas). Desde ahí ejecuto los pasos 3–7, te informo el costo real y elimino el Pod contigo.

## Archivos

- Mac: `tools/splat/preparar_paquete.sh`, `blender/scripts/empaquetar_splat.py`, `blender/scripts/camaras_splat.py`
  (OptiX, vistas de control), `tools/splat/verificar_poses.py`, `tools/splat/ply_sintetico.mjs`, `tools/splat/a_spz.mjs`.
- Nube: `nube/splat/{ejecutar,instalar,guardian}.sh`, `a_colmap.py`, `entrenar.py`, `metricas.py`.
- Visor: `apartamento-102/recorrido-splat.html`, `src/capa-splat.mjs`, `src/entrada-splat.mjs`,
  `tools/build_recorrido_splat.mjs`, `tools/capturar_control.mjs`, `tools/medir_splat.mjs`.
- Evidencia: `apartamento-102/capturas/splat-piloto/` (vista c10 en Cycles 16 muestras, V5 y splat **sintético** de
  prueba de alineación; parche de calibración; mediciones de fps, poses y línea base).
