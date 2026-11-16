import type { ChainNode } from "./chain";
export type PortSide = "top" | "right" | "bottom" | "left";
const directions = {
  top: [0, -1],
  right: [1, 0],
  bottom: [0, 1],
  left: [-1, 0],
} as const;
export function station(node: ChainNode, compact: boolean, placement: boolean) {
  const mobile: Record<string, number[]> = placement
    ? {
        sun: [60, 55, 86, 76],
        co2: [180, 55, 86, 76],
        water: [300, 55, 86, 76],
        photo: [180, 178, 174, 84],
        fuel: [180, 285, 170, 74],
        process: [180, 391, 158, 78],
        atp: [180, 492, 150, 52],
        cell: [309, 331, 94, 150],
      }
    : {
        sun: [60, 55, 86, 76],
        co2: [180, 55, 86, 76],
        water: [300, 55, 86, 76],
        photo: [180, 183, 174, 86],
        fuel: [90, 310, 145, 85],
        process: [270, 310, 150, 90],
        atp: [270, 485, 130, 112],
        cell: [90, 485, 140, 146],
      };
  const desktop: Record<string, number[]> = placement
    ? {
        sun: [125, 80, 225, 82],
        co2: [125, 200, 225, 82],
        water: [125, 320, 225, 82],
        photo: [470, 200, 270, 220],
        fuel: [780, 200, 195, 180],
        process: [1040, 200, 180, 165],
        atp: [1240, 200, 120, 185],
        cell: [1420, 200, 205, 240],
      }
    : {
        sun: [200, 70, 260, 82],
        co2: [200, 175, 260, 82],
        water: [200, 280, 260, 82],
        photo: [655, 170, 300, 230],
        fuel: [1040, 160, 230, 205],
        process: [1165, 490, 285, 180],
        atp: [820, 490, 170, 200],
        cell: [360, 490, 255, 220],
      };
  const base =
    node.label === "2 net ATP"
      ? undefined
      : (compact ? mobile : desktop)[node.id];
  if (base) return { x: base[0], y: base[1], width: base[2], height: base[3] };
  return {
    x: compact ? node.mx : node.x * 1.5,
    y: compact ? node.my : node.y,
    width:
      node.kind === "concept" ? (compact ? 150 : 340) : compact ? 110 : 200,
    height:
      node.kind === "concept" ? (compact ? 110 : 190) : compact ? 100 : 125,
  };
}
export function portSide(
  node: ChainNode,
  output: boolean,
  compact: boolean,
  placement = false,
): PortSide {
  if (compact) return output ? "bottom" : "top";
  if (node.label === "2 net ATP") return "left";
  if (!placement) {
    if (node.id === "fuel" && output) return "bottom";
    if (node.id === "process") return output ? "left" : "top";
    if (node.id === "atp" || node.id === "cell")
      return output ? "left" : "right";
  }
  return output ? "right" : "left";
}
export function portPoint(
  node: ChainNode,
  output: boolean,
  compact: boolean,
  placement = false,
) {
  const side = portSide(node, output, compact, placement),
    vector = directions[side],
    box = station(node, compact, placement);
  return {
    x: box.x + (vector[0] * box.width) / 2,
    y: box.y + (vector[1] * box.height) / 2,
    side,
  };
}
export function wirePath(
  a: { x: number; y: number; side: PortSide },
  b: { x: number; y: number; side: PortSide },
) {
  const from = directions[a.side],
    to = directions[b.side];
  const distance = Math.max(
    35,
    Math.min(110, Math.abs(b.x - a.x) / 2 + Math.abs(b.y - a.y) / 3),
  );
  return `M${a.x},${a.y} C${a.x + from[0] * distance},${a.y + from[1] * distance} ${b.x + to[0] * distance},${b.y + to[1] * distance} ${b.x},${b.y}`;
}
