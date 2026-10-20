/** Utilitaires pixel-precis pour brush en row-major Uint8Array. */

export interface BBox {
  x0: number;
  y0: number;
  x1: number; // inclusif
  y1: number; // inclusif
}

export function emptyBBox(): BBox {
  return { x0: Infinity, y0: Infinity, x1: -Infinity, y1: -Infinity };
}

export function expandBBox(bb: BBox, x: number, y: number): void {
  if (x < bb.x0) bb.x0 = x;
  if (y < bb.y0) bb.y0 = y;
  if (x > bb.x1) bb.x1 = x;
  if (y > bb.y1) bb.y1 = y;
}

export function isEmptyBBox(bb: BBox): boolean {
  return bb.x1 < bb.x0 || bb.y1 < bb.y0;
}

export function drawDisk(
  target: Uint8Array,
  w: number,
  h: number,
  cx: number,
  cy: number,
  radius: number,
  value: 0 | 1,
  dirty: BBox,
): void {
  const r = Math.max(0, radius | 0);
  const r2 = r * r;
  const x0 = Math.max(0, cx - r);
  const x1 = Math.min(w - 1, cx + r);
  const y0 = Math.max(0, cy - r);
  const y1 = Math.min(h - 1, cy + r);
  for (let y = y0; y <= y1; y++) {
    const dy = y - cy;
    const dy2 = dy * dy;
    for (let x = x0; x <= x1; x++) {
      const dx = x - cx;
      if (dx * dx + dy2 <= r2) {
        target[y * w + x] = value;
        expandBBox(dirty, x, y);
      }
    }
  }
}

export function drawSegment(
  target: Uint8Array,
  w: number,
  h: number,
  ax: number,
  ay: number,
  bx: number,
  by: number,
  radius: number,
  value: 0 | 1,
  dirty: BBox,
): void {
  const dx = bx - ax;
  const dy = by - ay;
  const dist = Math.hypot(dx, dy);
  const steps = Math.max(1, Math.ceil(dist));
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    drawDisk(target, w, h, Math.round(ax + dx * t), Math.round(ay + dy * t), radius, value, dirty);
  }
}

/** Retourne (before, after, [x0, y0, w, h]) sur la bbox dilatée par le rayon. */
export function snapshotBBox(
  before: Uint8Array,
  after: Uint8Array,
  w: number,
  bbox: BBox,
): { before: Uint8Array; after: Uint8Array; bbox: [number, number, number, number] } {
  const bw = bbox.x1 - bbox.x0 + 1;
  const bh = bbox.y1 - bbox.y0 + 1;
  const beforeBuf = new Uint8Array(bw * bh);
  const afterBuf = new Uint8Array(bw * bh);
  for (let yy = 0; yy < bh; yy++) {
    for (let xx = 0; xx < bw; xx++) {
      const src = (bbox.y0 + yy) * w + (bbox.x0 + xx);
      const dst = yy * bw + xx;
      beforeBuf[dst] = before[src];
      afterBuf[dst] = after[src];
    }
  }
  return { before: beforeBuf, after: afterBuf, bbox: [bbox.x0, bbox.y0, bw, bh] };
}
