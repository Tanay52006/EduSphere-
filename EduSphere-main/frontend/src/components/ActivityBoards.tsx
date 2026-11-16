import { useEffect, useRef, useState } from "react";
import type { ActivityDraft, ActivitySession } from "../lib/activities";
import { ChainBoard } from "./ChainBoard";

export function ActivityBoards({
  game,
  draft,
  edit,
  locked,
  feedback,
}: {
  game: ActivitySession;
  draft: ActivityDraft;
  edit: (next: ActivityDraft) => void;
  locked: boolean;
  feedback: ActivitySession["feedback"];
}) {
  const [selected, setSelected] = useState<string | null>(null);
  const cardRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const focusAfterEdit = useRef<string | null>(null);
  const items = game.activity.items;
  const columns = Math.ceil(items.length / 2);
  const names = Object.fromEntries(items.map((item) => [item.id, item.label]));
  useEffect(() => {
    if (focusAfterEdit.current)
      cardRefs.current[focusAfterEdit.current]?.focus();
    focusAfterEdit.current = null;
  }, [draft]);
  const move = (from: string, to: string) => {
    if (from === to || locked) return;
    const order = draft.order.filter((key) => key !== from);
    order.splice(draft.order.indexOf(to), 0, from);
    focusAfterEdit.current = from;
    edit({ ...draft, order });
    setSelected(null);
  };
  const place = (key: string, bucket: string) => {
    if (locked) return;
    focusAfterEdit.current =
      items.find((item) => item.id !== key && !draft.assignments[item.id])
        ?.id ?? key;
    edit({ ...draft, assignments: { ...draft.assignments, [key]: bucket } });
    setSelected(null);
  };
  if (game.activity.mechanic === "connections") {
    return (
      <div className="board-run">
        <ChainBoard
          nodes={items.map((item, i) => ({
            ...item,
            kind: "concept",
            input: true,
            output: true,
            x: 140 + (i % columns) * (740 / (columns - 1)),
            y: 150 + Math.floor(i / columns) * 300,
            mx: 90 + (i % 2) * 180,
            my: 100 + Math.floor(i / 2) * 180,
          }))}
          links={draft.links}
          process={null}
          placement={false}
          selected={selected}
          onSelect={setSelected}
          onConnect={(a, b) => {
            if (a !== b && !draft.links.some(([x, y]) => x === a && y === b))
              edit({ ...draft, links: [...draft.links, [a, b]] });
            setSelected(null);
          }}
          onRemove={(i) =>
            edit({
              ...draft,
              links: draft.links.filter((_, index) => index !== i),
            })
          }
          feedback={feedback}
          locked={locked}
        />
      </div>
    );
  }
  if (game.activity.mechanic === "sequence") {
    return (
      <div className="sequence-board">
        <p className="activity-instruction">
          Tap a card, then its new position. Or use the arrows.
        </p>
        <ol aria-label="Your sequence">
          {draft.order.map((key, i) => (
            <li
              key={key}
              className={`${feedback?.misplaced.includes(key) ? "piece-retry" : ""} ${selected === key ? "piece-selected" : ""}`}
            >
              <span className="sequence-position" aria-hidden="true">
                {i + 1}
              </span>
              <button
                className="sequence-card"
                ref={(element) => {
                  cardRefs.current[key] = element;
                }}
                disabled={locked}
                onKeyDown={(event) => {
                  const target =
                    i +
                    (event.key === "ArrowUp"
                      ? -1
                      : event.key === "ArrowDown"
                        ? 1
                        : 0);
                  if (
                    target !== i &&
                    target >= 0 &&
                    target < draft.order.length
                  ) {
                    event.preventDefault();
                    move(key, draft.order[target]);
                  }
                }}
                aria-pressed={selected === key}
                onClick={() =>
                  selected && selected !== key
                    ? move(selected, key)
                    : setSelected(selected === key ? null : key)
                }
              >
                {names[key]}
              </button>
              <div className="sequence-arrows">
                <button
                  disabled={locked || i === 0}
                  aria-label={`Move ${names[key]} up`}
                  onClick={() => move(key, draft.order[i - 1])}
                >
                  ↑
                </button>
                <button
                  disabled={locked || i === draft.order.length - 1}
                  aria-label={`Move ${names[key]} down`}
                  onClick={() => move(key, draft.order[i + 1])}
                >
                  ↓
                </button>
              </div>
            </li>
          ))}
        </ol>
      </div>
    );
  }
  const card = (key: string) => (
    <button
      key={key}
      ref={(element) => {
        cardRefs.current[key] = element;
      }}
      className={`sort-card ${selected === key ? "piece-selected" : ""} ${feedback?.misplaced.includes(key) ? "piece-retry" : ""}`}
      disabled={locked}
      aria-pressed={selected === key}
      onClick={() => setSelected(selected === key ? null : key)}
    >
      {names[key]}
    </button>
  );
  return (
    <div className="sort-board">
      <p className="activity-instruction">
        Choose a sample, then its group. You can move it again any time.
      </p>
      <div className="sort-tray" aria-label="Unsorted samples">
        {items
          .filter((item) => !draft.assignments[item.id])
          .map((item) => card(item.id))}
        {Object.keys(draft.assignments).length === items.length && (
          <span>All samples placed. Check your rule.</span>
        )}
      </div>
      <div className="sort-groups">
        {game.activity.buckets.map((bucket) => (
          <section key={bucket.id} aria-label={`${bucket.label} group`}>
            <button
              className="sort-group-target"
              disabled={locked || !selected}
              aria-label={`Place selected sample in ${bucket.label}`}
              onClick={() => selected && place(selected, bucket.id)}
            >
              <strong>{bucket.label}</strong>
              <span aria-hidden="true">+</span>
            </button>
            <p>{bucket.rule}</p>
            <div>
              {items
                .filter((item) => draft.assignments[item.id] === bucket.id)
                .map((item) => card(item.id))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
