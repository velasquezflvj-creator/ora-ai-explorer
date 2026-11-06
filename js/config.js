/* Ora AI — Explorador de torres
 * Todo lo que se edita (marca, textos, planos de fachada, tiempos del video) vive aquí.
 *
 * Planos de fachada: cada plano es un cuadrilátero [arriba-izq, arriba-der, abajo-der, abajo-izq]
 * en píxeles de la imagen original (1672×941). Los pisos se reparten con una homografía,
 * así la perspectiva de la foto (sobre todo en el atardecer) queda bien repartida.
 * Para recalibrar abre la página con ?debug=1.
 */
window.ORA = {
  brand: {
    name: 'ORA AI',
    tag: 'Explorador de torres',
    cta: { label: 'Tour privado', href: '#' },   // pon aquí el link de Calendly / WhatsApp
  },

  // Texto de ayuda y aviso legal
  copy: {
    hint: 'Pasa el cursor por un piso para explorar',
    hintTouch: 'Toca un piso para explorar',
    legal: 'Demo conceptual · imágenes ilustrativas · Ora AI',
  },

  towers: {
    T1: { name: 'Torre 1', floors: 15, base: 2, pent: 2 },   // pisos 2–16, los 2 últimos son penthouse
    T2: { name: 'Torre 2', floors: 16, base: 2, pent: 2 },
  },

  images: {
    day: {
      label: 'Atardecer',
      src: 'img/day.webp',
      focus: [0.5, 0.5],
      planes: [
        { id: 'T1',  tower: 'T1', quad: [[565, -5], [800, 100], [794, 700], [514, 775]] },
        { id: 'T2L', tower: 'T2', quad: [[866, 72], [1005, 172], [1005, 545], [866, 545]] },
        { id: 'T2R', tower: 'T2', quad: [[1008, 173], [1222, 200], [1248, 545], [1008, 543]] },
      ],
      pins: [
        { x: 850,  y: 826, label: 'Piscina y jacuzzi' },
        { x: 1340, y: 770, label: 'Zonas verdes' },
        { x: 1255, y: 586, label: 'Acceso principal' },
      ],
    },
    night: {
      label: 'Noche',
      src: 'img/night.webp',
      focus: [0.5, 0.5],
      planes: [
        { id: 'T1',  tower: 'T1', quad: [[240, 213], [601, 243], [603, 702], [240, 708]] },
        { id: 'T2L', tower: 'T2', quad: [[721, 52], [994, 80], [994, 575], [721, 572]] },
        { id: 'T2R', tower: 'T2', quad: [[1000, 75], [1376, -3], [1376, 596], [1000, 566]] },
      ],
      pins: [
        { x: 335,  y: 800, label: 'Piscina' },
        { x: 800,  y: 820, label: 'Zonas verdes' },
        { x: 1345, y: 655, label: 'Acceso principal' },
      ],
    },
  },

  /* Unidades. Los tiempos (en segundos) son del clip de video:
   *  plan.hold   → fotograma donde se pausa la maqueta y aparece el panel
   *  plan.resume → desde dónde sigue el video cuando eliges una habitación
   *  rooms[].hold → fotograma estático de cada habitación
   */
  units: {
    res: {
      name: 'Residencia A',
      status: 'DISPONIBLE',
      beds: 2, baths: '2', area: 135,
      specs: '2 hab · 2 baños · 135 m²',
      desc: 'Residencia de dos habitaciones con muro de vidrio de piso a techo, cocina abierta y suite principal con baño tipo spa y vestier. Incluye balcón.',
      clip: 'media/interior-residencia.mp4',
      plan: { hold: 0.54, resume: 1.15 },
      rooms: [
        { label: 'Sala y cocina',        hold: 3.50 },
        { label: 'Habitación principal', hold: 4.80 },
        { label: 'Baño principal',       hold: 5.80 },
      ],
    },
    pent: {
      name: 'Penthouse',
      status: 'EXCLUSIVO',
      beds: 3, baths: '3½', area: 297,
      specs: '3 hab · 3½ baños · 297 m²',
      desc: 'Penthouse esquinero con terraza envolvente, gran sala con vistas panorámicas, cocina de chef y baño spa. Tres habitaciones y servicio.',
      clip: 'media/interior-penthouse.mp4',
      plan: { hold: 0.60, resume: 1.55 },
      rooms: [
        { label: 'Gran sala',       hold: 2.10 },
        { label: 'Cocina del chef', hold: 3.05 },
        { label: 'Baño spa',        hold: 3.70 },
      ],
    },
  },
};
