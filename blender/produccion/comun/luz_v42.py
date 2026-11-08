# Iluminación V4.2 definitiva (propuesta aprobada en dirección a partir de la referencia visual), compartida por
# v4/v4_2_final.py (C4) y rediseno_sala/rediseno_sala_v2_no_ejecutado.py (C3) para que ambos usen exactamente la misma luz.
# Apartamento 102: propuesta de redistribución conceptual (no planta verificada).
#
# Parte de escena_v4_2_prueba3 (sol existente a 18° de elevación y 85° de azimut, luz ambiental real 0,6) y aplica los dos
# cambios pendientes de la prueba 3: sol cálido (3800 K, sol bajo de tarde coherente con 18°) y luz ambiental real 0,35 para
# que las sombras bajen hacia p5 0,20–0,24. Focos, materiales, balance de blancos (4600 K) y AgX no cambian.
import math
from mathutils import Vector

SOL_ELEV, SOL_AZ = 18.0, 85.0          # grados; entra por el vano de la puerta-ventana de la sala (verificado sin fugas)
SOL_K = 3800.0
FONDO_LUZ = 0.35                       # nodo «Fondo» = luz ambiental real (rayos que no son de cámara)
OBJETIVO = {'p50': (0.50, 0.55), 'quemado_max_%': 1.0, 'p5': (0.20, 0.24)}


def direccion_sol(sol):
    d = (sol.rotation_euler.to_matrix() @ Vector((0, 0, -1))).normalized()
    return round(math.degrees(math.asin(-d.z)), 2), round(math.degrees(math.atan2(d.y, d.x)), 2)


def aplicar(sc, cambio=lambda p, a, b: None):
    """Aplica la luz V4.2 definitiva. Exige el estado de partida de la prueba 3 (falla si la escena no es la esperada)."""
    sol = sc.objects['Sol_HDRI']; d = sol.data
    elev, az = direccion_sol(sol)
    if sol.hide_render or abs(elev - SOL_ELEV) > 0.05 or abs(az - SOL_AZ) > 0.05:
        raise RuntimeError(f'Sol_HDRI no está en el estado de la prueba 3 (visible a {SOL_ELEV}°/{SOL_AZ}°): {elev}°/{az}°, oculto={sol.hide_render}')
    antes_k = d.temperature if d.use_temperature else f'color {[round(c, 2) for c in d.color]}'
    d.use_temperature = True; d.temperature = SOL_K; d.color = (1.0, 1.0, 1.0)
    cambio('Sol_HDRI: color', antes_k, f'{SOL_K:.0f} K (cuerpo negro)')
    fondo = sc.world.node_tree.nodes['Fondo']
    a = round(fondo.inputs['Strength'].default_value, 3); fondo.inputs['Strength'].default_value = FONDO_LUZ
    cambio('luz ambiental real (Fondo, fuerza)', a, FONDO_LUZ)
    focos = {(round(o.data.energy, 2), o.data.temperature) for o in sc.objects
             if o.type == 'LIGHT' and o.data.type == 'SPOT' and o.name.startswith('Luz_')}
    vs = sc.view_settings
    return {'sol': {'elevacion': elev, 'azimut': az, 'energia': d.energy, 'K': SOL_K}, 'fondo': FONDO_LUZ,
            'focos': sorted(map(list, focos)), 'vista': [vs.view_transform, vs.look], 'wb_K': round(vs.white_balance_temperature)}


APROBADOS_V42 = {   # parámetros de V4.2 que deben conservarse (estado de la prueba 3)
    'focos_W_K': [[9.0, 3600.0]], 'wb_K': 4600, 'vista': ['AgX', 'AgX - Medium High Contrast'], 'sol_energia': 4.0,
}


def verificar(sc):
    """Comprueba de forma explícita cada parámetro de la luz V4.2 definitiva y los parámetros aprobados que no cambian.
    Devuelve una lista de {parametro, esperado, actual, ok}; lanza RuntimeError si alguno no coincide."""
    sol = sc.objects['Sol_HDRI']; d = sol.data; elev, az = direccion_sol(sol); vs = sc.view_settings
    focos = sorted(map(list, {(round(o.data.energy, 2), o.data.temperature) for o in sc.objects
                              if o.type == 'LIGHT' and o.data.type == 'SPOT' and o.name.startswith('Luz_')}))
    filas = [
        ('Sol_HDRI visible en render', True, not sol.hide_render),
        ('Sol_HDRI usa temperatura de color', True, bool(d.use_temperature)),
        ('Sol_HDRI temperatura (K)', SOL_K, round(d.temperature, 1)),
        ('Sol_HDRI elevación (°)', SOL_ELEV, round(elev, 1)),
        ('Sol_HDRI azimut (°)', SOL_AZ, round(az, 1)),
        ('Sol_HDRI energía', APROBADOS_V42['sol_energia'], round(d.energy, 3)),
        ('Fondo (luz ambiental real)', FONDO_LUZ, round(sc.world.node_tree.nodes['Fondo'].inputs['Strength'].default_value, 4)),
        ('Focos Luz_* (W, K)', APROBADOS_V42['focos_W_K'], focos),
        ('Balance de blancos (K)', APROBADOS_V42['wb_K'], round(vs.white_balance_temperature)),
        ('Transformación de vista', APROBADOS_V42['vista'], [vs.view_transform, vs.look]),
    ]
    res = [{'parametro': p, 'esperado': e, 'actual': a, 'ok': e == a} for p, e, a in filas]
    malos = [r for r in res if not r['ok']]
    if malos: raise RuntimeError('luz V4.2 no verificada: ' + '; '.join(f"{r['parametro']} = {r['actual']} (esperado {r['esperado']})" for r in malos))
    return res


def calibrar_exposicion(sc, medir, inicio=None):
    """Exposición solo de vista (sin re-render): mediana 0,50–0,55 y superficies quemadas ≤ 1 %. `medir()` devuelve
    {'p5','p50','p95','quemado_%'} del Render Result con la vista actual."""
    vs = sc.view_settings; ev = vs.exposure if inicio is None else inicio; hist = []
    for _ in range(24):
        vs.exposure = ev; m = medir(); hist.append({'exp': round(ev, 3), **m})
        if m['quemado_%'] > OBJETIVO['quemado_max_%'] or m['p50'] > OBJETIVO['p50'][1]: ev -= 0.05
        elif m['p50'] < OBJETIVO['p50'][0]: ev += 0.05
        else: break
    vs.exposure = ev
    return hist
