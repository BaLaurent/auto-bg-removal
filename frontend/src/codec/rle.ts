// Port JS de pycocotools/_mask.pyx (rleFromString / rleToString) + bitmap I/O Fortran-order.
// Le format COCO scanne column-major : counts[0] = nb de 0 initiaux en parcours colonne par colonne,
// counts[1] = nb de 1 suivants, etc.

function rleFromString(s: string): number[] {
  const m = s.length;
  const cnts: number[] = [];
  let p = 0;
  while (p < m) {
    let x = 0;
    let k = 0;
    let more = 1;
    while (more) {
      const c = s.charCodeAt(p) - 48;
      x |= (c & 0x1f) << (5 * k);
      more = c & 0x20;
      p++;
      k++;
      if (!more && c & 0x10) {
        x |= ~0 << (5 * k);
      }
    }
    if (cnts.length > 2) x += cnts[cnts.length - 2];
    cnts.push(x);
  }
  return cnts;
}

function rleToString(cnts: number[]): string {
  const out: string[] = [];
  for (let i = 0; i < cnts.length; i++) {
    let x = cnts[i];
    if (i > 2) x -= cnts[i - 2];
    let more = 1;
    while (more) {
      let c = x & 0x1f;
      x >>= 5;
      if (c & 0x10) more = x !== -1 ? 1 : 0;
      else more = x !== 0 ? 1 : 0;
      if (more) c |= 0x20;
      c += 48;
      out.push(String.fromCharCode(c));
    }
  }
  return out.join("");
}

/** Décode un RLE COCO base64 en bitmap row-major Uint8Array de taille h*w. */
export function decodeRLE(countsB64: string, h: number, w: number): Uint8Array {
  const decoded = atob(countsB64);
  const cnts = rleFromString(decoded);
  const out = new Uint8Array(h * w);
  let val: 0 | 1 = 0;
  let pos = 0;
  for (const c of cnts) {
    if (val) {
      // remplir c pixels en column-major
      for (let i = 0; i < c; i++) {
        const col = (pos / h) | 0;
        const row = pos - col * h;
        out[row * w + col] = 1;
        pos++;
      }
    } else {
      pos += c;
    }
    val = (val ^ 1) as 0 | 1;
  }
  return out;
}

/** Encode un bitmap row-major (Uint8Array h*w) en RLE COCO base64 (column-major). */
export function encodeRLE(mask: Uint8Array, h: number, w: number): string {
  const total = h * w;
  const cnts: number[] = [];
  let val = 0;
  let count = 0;
  for (let pos = 0; pos < total; pos++) {
    const col = (pos / h) | 0;
    const row = pos - col * h;
    const v = mask[row * w + col] ? 1 : 0;
    if (v === val) {
      count++;
    } else {
      cnts.push(count);
      count = 1;
      val = v;
    }
  }
  cnts.push(count);
  return btoa(rleToString(cnts));
}
