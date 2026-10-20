/** Translation entre coordonnées DOM (canvas) et coordonnées image (pixels source).
 *
 * L'image est rendue en "contain" dans le viewport : on scale au plus grand
 * facteur qui rentre, on centre, et les bandes hors image sont ignorées.
 */

export interface Viewport {
  /** Dimensions du canvas DOM (en pixels CSS). */
  domW: number;
  domH: number;
  /** Dimensions de l'image source. */
  imageW: number;
  imageH: number;
}

export interface Mapping {
  scale: number; // 1 px image = `scale` px DOM
  offsetX: number; // px DOM
  offsetY: number;
}

export function computeMapping(v: Viewport): Mapping {
  if (!v.imageW || !v.imageH) return { scale: 1, offsetX: 0, offsetY: 0 };
  const scale = Math.min(v.domW / v.imageW, v.domH / v.imageH);
  const offsetX = (v.domW - v.imageW * scale) / 2;
  const offsetY = (v.domH - v.imageH * scale) / 2;
  return { scale, offsetX, offsetY };
}

export function domToImage(v: Viewport, x: number, y: number): { x: number; y: number } | null {
  const m = computeMapping(v);
  const ix = (x - m.offsetX) / m.scale;
  const iy = (y - m.offsetY) / m.scale;
  if (ix < 0 || iy < 0 || ix >= v.imageW || iy >= v.imageH) return null;
  return { x: Math.floor(ix), y: Math.floor(iy) };
}

export function imageToDom(v: Viewport, x: number, y: number): { x: number; y: number } {
  const m = computeMapping(v);
  return { x: x * m.scale + m.offsetX, y: y * m.scale + m.offsetY };
}
