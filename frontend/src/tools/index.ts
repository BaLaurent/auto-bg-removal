import type { Tool } from "../state";
import { createBoxTool, type BoxToolDeps } from "./boxTool";
import { createBrushTool } from "./brushTool";
import { createPointsTool } from "./pointsTool";
import type { ToolHandlers } from "./types";

export type { ImgPointerEvent, ToolHandlers } from "./types";

export function createToolHandlers(tool: Tool, deps: BoxToolDeps): ToolHandlers {
  switch (tool) {
    case "points":
      return createPointsTool();
    case "box":
      return createBoxTool(deps);
    case "brush_add":
      return createBrushTool("add");
    case "brush_erase":
      return createBrushTool("erase");
  }
}
