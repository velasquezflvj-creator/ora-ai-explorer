// Unidades sintéticas de escena. No son cotas ni medidas de los DWG.
export const bounds = { minX: -5.75, maxX: 5.75, minZ: -4.75, maxZ: 4.75 };
export function box(x, z, width, depth) {
  return { minX: x - width / 2, maxX: x + width / 2, minZ: z - depth / 2, maxZ: z + depth / 2 };
}
export function canOccupy(x, z, obstacles, radius = .24) {
  if (x < bounds.minX || x > bounds.maxX || z < bounds.minZ || z > bounds.maxZ) return false;
  return !obstacles.some(b => x > b.minX - radius && x < b.maxX + radius && z > b.minZ - radius && z < b.maxZ + radius);
}
export function moveWithCollisions(position, dx, dz, obstacles) {
  // Subpasos contra el efecto túnel; separación por ejes permite deslizarse por muros.
  const steps = Math.max(1, Math.ceil(Math.hypot(dx, dz) / .08));
  let { x, z } = position;
  for (let i = 0; i < steps; i++) {
    if (canOccupy(x + dx / steps, z, obstacles)) x += dx / steps;
    if (canOccupy(x, z + dz / steps, obstacles)) z += dz / steps;
  }
  return { x, z };
}
