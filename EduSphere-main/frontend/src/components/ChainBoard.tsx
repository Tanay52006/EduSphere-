import { useEffect, useRef, useState, type PointerEvent } from "react";
import type { ChainNode, LinkPair } from "../lib/chain";
import { BiologyArt } from "./BiologyArt";
import { ArenaIcon } from "./ArenaIcon";
import { portPoint, portSide, wirePath, station } from "../lib/chainGeometry";

export function ChainBoard({
  nodes,
  links,
  process,
  placement,
  onPlace,
  prediction,
  predictionOptions = [],
  onPredict,
  selected,
  onSelect,
  onConnect,
  onRemove,
  feedback,
  locked,
}: {
  nodes: ChainNode[];
  links: LinkPair[];
  process: string | null;
  placement: boolean;
  onPlace?: (process: string) => void;
  prediction?: string | null;
  predictionOptions?: string[];
  onPredict?: (node: string) => void;
  selected: string | null;
  onSelect: (id: string | null) => void;
  onConnect: (from: string, to: string) => void;
  onRemove: (index: number) => void;
  feedback: {
    correct: boolean;
    broken: LinkPair | null;
    powered: LinkPair[];
    stalled?: string | null;
  } | null;
  locked: boolean;
}) {
  const dragged = useRef(false);
  const board = useRef<HTMLDivElement>(null);
  const [compact, setCompact] = useState(window.innerWidth < 1050);
  const [drag, setDrag] = useState<{
    from: string;
    x: number;
    y: number;
  } | null>(null);
  useEffect(() => {
    const container = board.current?.closest(".chain-play") ?? board.current;
    const resize = () =>
      setCompact((container?.clientWidth ?? window.innerWidth) <= 900);
    resize();
    const observer =
      typeof ResizeObserver !== "undefined" ? new ResizeObserver(resize) : null;
    if (container) observer?.observe(container);
    window.addEventListener("resize", resize);
    return () => {
      observer?.disconnect();
      window.removeEventListener("resize", resize);
    };
  }, []);
  const w = compact ? 360 : 1540,
    h = compact
      ? nodes.every((node) => node.kind === "concept")
        ? Math.ceil(nodes.length / 2) * 180 + 20
        : 570
      : placement
        ? 500
        : 600;
  const point = (node: ChainNode, output: boolean) =>
    portPoint(node, output, compact, placement);
  const curve = wirePath;
  const endDrag = (event: PointerEvent<HTMLButtonElement>) => {
    if (!drag) return;
    const hit = document
      .elementFromPoint(event.clientX, event.clientY)
      ?.closest<HTMLElement>("[data-input]");
    if (hit?.dataset.input) onConnect(drag.from, hit.dataset.input);
    setDrag(null);
  };
  return (
    <div
      ref={board}
      className={`chain-board ${compact ? "board-compact" : ""} ${placement ? "board-placement" : ""} ${feedback?.correct ? "board-powered" : ""}`}
      style={{ aspectRatio: `${w}/${h}` }}
    >
      <svg className="chain-wires" viewBox={`0 0 ${w} ${h}`} aria-hidden="true">
        {links.map(([from, to], index) => {
          if (placement && compact && to === "cell") return null;
          const a = nodes.find((n) => n.id === from),
            b = nodes.find((n) => n.id === to);
          if (!a || !b) return null;
          const broken =
            feedback?.broken?.[0] === from && feedback?.broken?.[1] === to;
          const powered = feedback?.powered.some(
            ([s, t]) => s === from && t === to,
          );
          return (
            <g
              key={`${from}-${to}`}
              className={`wire ${!locked && !placement ? "wire-editable" : ""} ${broken ? "wire-broken" : powered ? "wire-powered" : ""}`}
              onClick={
                !locked && !placement ? () => onRemove(index) : undefined
              }
            >
              <path
                className="wire-base"
                d={curve(point(a, true), point(b, false))}
              />
              <path
                className="wire-flow"
                d={curve(point(a, true), point(b, false))}
              />
              {!locked && !placement && (
                <path
                  className="wire-hit"
                  data-connection={`${from}:${to}`}
                  d={curve(point(a, true), point(b, false))}
                >
                  <title>
                    Remove {a.label} → {b.label}
                  </title>
                </path>
              )}
            </g>
          );
        })}
        {drag && (
          <path
            className="wire-drag"
            d={curve(
              point(
                nodes.find((n) => n.id === drag.from)!,
                true,
              ),
              { x: drag.x, y: drag.y, side: "top" },
            )}
          />
        )}
      </svg>
      {nodes.map((node) => {
        const box = station(node, compact, placement);
        const slot = placement && node.id === "process";
        const kind = slot
          ? process === "respiration"
            ? "mitochondria"
            : process === "fermentation"
              ? "flask"
              : process
                ? "digestion"
                : "slot"
          : node.kind === "molecule" && node.id !== "co2"
            ? "cofactor"
            : node.kind;
        return (
          <div
            key={node.id}
            onDragOver={
              slot && !locked ? (event) => event.preventDefault() : undefined
            }
            onDrop={
              slot && !locked
                ? (event) => {
                    event.preventDefault();
                    const value = event.dataTransfer.getData(
                      "application/edusphere-process",
                    );
                    if (
                      ["respiration", "digestion", "fermentation"].includes(
                        value,
                      )
                    )
                      onPlace?.(value);
                  }
                : undefined
            }
            className={`chain-station node-${node.id} station-${kind} ${selected === node.id ? "station-selected" : ""} ${feedback?.stalled === node.id ? "station-stalled" : ""} ${prediction === node.id ? "station-predicted" : ""}`}
            style={{
              left: `${(box.x / w) * 100}%`,
              top: `${(box.y / h) * 100}%`,
              width: `${(box.width / w) * 100}%`,
              height: `${(box.height / h) * 100}%`,
            }}
          >
            {predictionOptions.includes(node.id) && (
              <button
                className="prediction-hit"
                aria-label={`Predict: ${node.label} produces ATP`}
                aria-describedby="prediction-prompt"
                aria-pressed={prediction === node.id}
                disabled={locked}
                onClick={() => onPredict?.(node.id)}
              >
                <span aria-hidden="true">⚡</span>
              </button>
            )}
            {node.input && (
              <button
                className={`station-port input-port port-${portSide(node, false, compact, placement)}`}
                data-input={node.id}
                disabled={locked || placement}
                aria-label={`Connect to ${node.label}`}
                onClick={() => selected && onConnect(selected, node.id)}
              >
                <span />
              </button>
            )}
            <div className="station-face">
              {kind === "slot" ? (
                <span className="slot-plus">+</span>
              ) : kind === "concept" ? (
                <span className="concept-token" aria-hidden="true">
                  <ArenaIcon name="paths" size={17} />
                </span>
              ) : (
                <BiologyArt kind={kind} size={compact ? 62 : 130} />
              )}
              <strong>
                {slot ? (
                  process ? (
                    process[0].toUpperCase() + process.slice(1)
                  ) : (
                    "Choose a process"
                  )
                ) : node.id === "water" ? (
                  <>
                    <span className="compact-label">H₂O</span>
                    <span className="wide-label">Water</span>
                  </>
                ) : (
                  node.label
                )}
              </strong>
            </div>
            {node.output && (
              <button
                className={`station-port output-port port-${portSide(node, true, compact, placement)}`}
                disabled={locked || placement}
                aria-pressed={selected === node.id}
                aria-label={`Connect from ${node.label}`}
                onClick={(event) => {
                  if (event.detail && dragged.current) {
                    dragged.current = false;
                    return;
                  }
                  onSelect(selected === node.id ? null : node.id);
                }}
                onPointerDown={(event) => {
                  if (event.button !== 0) return;
                  dragged.current = false;
                  event.currentTarget.setPointerCapture(event.pointerId);
                  const box = event.currentTarget
                    .closest(".chain-board")!
                    .getBoundingClientRect();
                  setDrag({
                    from: node.id,
                    x: ((event.clientX - box.left) / box.width) * w,
                    y: ((event.clientY - box.top) / box.height) * h,
                  });
                }}
                onPointerMove={(event) => {
                  if (!drag) return;
                  dragged.current = true;
                  const box = event.currentTarget
                    .closest(".chain-board")!
                    .getBoundingClientRect();
                  setDrag({
                    ...drag,
                    x: ((event.clientX - box.left) / box.width) * w,
                    y: ((event.clientY - box.top) / box.height) * h,
                  });
                }}
                onPointerUp={endDrag}
                onPointerCancel={() => setDrag(null)}
              >
                <span />
              </button>
            )}
          </div>
        );
      })}
      {selected && !drag && (
        <div className="connection-cue" role="status">
          Now choose an input{" "}
          <button onClick={() => onSelect(null)} aria-label="Cancel connection">
            ×
          </button>
        </div>
      )}
      {!locked && !placement && links.length > 0 && (
        <details className="connection-list">
          <summary>
            <ArenaIcon name="paths" size={15} />
            {links.length} links
          </summary>
          <div>
            {links.map(([from, to], i) => (
              <button
                key={`${from}-${to}`}
                onClick={() => onRemove(i)}
                aria-label={`Remove ${nodes.find((n) => n.id === from)?.label} to ${nodes.find((n) => n.id === to)?.label}`}
              >
                <span>
                  {nodes.find((n) => n.id === from)?.label} →{" "}
                  {nodes.find((n) => n.id === to)?.label}
                </span>
                <span aria-hidden="true">×</span>
              </button>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
