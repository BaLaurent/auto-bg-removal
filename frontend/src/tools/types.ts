export interface ImgPointerEvent {
  /** Coords image (entiers). null si pointer hors image (bandes). */
  pt: { x: number; y: number } | null;
  shiftKey: boolean;
  altKey: boolean;
  /** Bouton primaire pressé. */
  primary: boolean;
}

export interface ToolHandlers {
  onPointerDown?(e: ImgPointerEvent): void;
  onPointerMove?(e: ImgPointerEvent): void;
  onPointerUp?(e: ImgPointerEvent): void;
}
