"""Entrena el splat con el entrenador de referencia de gsplat 1.5.3 (examples/simple_trainer.py), configurado por
código para no depender de la sintaxis de banderas de la línea de órdenes.

    python entrenar.py <datos> <resultados> [--pasos 30000] [--max-gaussianas 1000000] [--prueba]

Estrategia MCMC (Kheradmand et al., 2024; la variante «mcmc» del propio gsplat) con TOPE de gaussianas: medido en el
MacBook Air M2 con Spark, ~1,5 M gaussianas dan 20 fps a densidad Retina y 37 fps a densidad 1,0; ~0,8 M, 50 fps.
Por eso el tope por defecto es 1 000 000 (ver docs/gaussian-splatting-nube.md).

<datos> contiene images/ y sparse/0 (de a_colmap.py). Importante:
  - normalize_world_space = False: el splat queda en metros y en los ejes de Blender (se alinea con el GLB del visor).
  - test_every muy grande: se entrena con TODAS las vistas; la evaluación objetiva se hace con las vistas de control
    (que nunca se entrenan) en metricas.py.
  - --prueba: 300 pasos, para la prueba de humo (minutos, centavos).
"""
import os, sys

GSPLAT = os.environ.get('GSPLAT_EJEMPLOS', '/workspace/ora/gsplat/examples')
sys.path.insert(0, GSPLAT); os.chdir(GSPLAT)   # el entrenador importa sus módulos vecinos (datasets, utils, ...)
import simple_trainer as st  # noqa: E402
from gsplat.strategy import MCMCStrategy  # noqa: E402

datos, resultados = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
args = sys.argv[3:]
pasos = int(args[args.index('--pasos') + 1]) if '--pasos' in args else 30000
if '--prueba' in args: pasos = 300
tope = int(args[args.index('--max-gaussianas') + 1]) if '--max-gaussianas' in args else 1_000_000

cfg = st.Config(init_opa=0.5, init_scale=0.1, opacity_reg=0.01, scale_reg=0.01, strategy=MCMCStrategy(cap_max=tope, verbose=True))   # = preset «mcmc» de gsplat
cfg.data_dir = datos; cfg.result_dir = resultados; cfg.data_factor = 1
cfg.normalize_world_space = False; cfg.test_every = 10 ** 6
cfg.disable_viewer = True; cfg.disable_video = True
cfg.max_steps = pasos
cfg.eval_steps = [pasos]; cfg.save_steps = sorted({min(7000, pasos), pasos}); cfg.ply_steps = [pasos]; cfg.save_ply = True
cfg.adjust_steps(cfg.steps_scaler)
print(f'[entrenar] datos={datos} resultados={resultados} pasos={pasos} tope={tope}', flush=True)
st.cli(st.main, cfg, verbose=True)
