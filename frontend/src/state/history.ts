import type { PointDTO } from "../api";

export interface OpSam {
  kind: "sam";
  samBeforeRle: string | null; // null = mask vide
  samAfterRle: string | null;
  pointsBefore: PointDTO[];
  pointsAfter: PointDTO[];
}

export interface OpStroke {
  kind: "stroke";
  layer: "add" | "erase";
  bbox: [number, number, number, number]; // x0, y0, w, h (inclusif)
  before: Uint8Array; // taille w*h
  after: Uint8Array;
}

export type Op = OpSam | OpStroke;

export const HISTORY_LIMIT = 50;

export function pushOp(stack: Op[], index: number, op: Op): { stack: Op[]; index: number } {
  // tronque les ops après l'index courant (branche redo coupée)
  const head = stack.slice(0, index);
  head.push(op);
  while (head.length > HISTORY_LIMIT) head.shift();
  return { stack: head, index: head.length };
}
