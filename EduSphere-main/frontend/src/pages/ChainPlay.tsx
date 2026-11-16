import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { chain, type ChainSession, type LinkPair } from "../lib/chain";
import { ChainBoard } from "../components/ChainBoard";
import { BiologyArt } from "../components/BiologyArt";
import { ArenaIcon } from "../components/ArenaIcon";
import { LearningError } from "../components/LearningUI";
import { Button, Skeleton } from "../components/ui";

export function ChainPlay({ sessionId }: { sessionId: string }) {
  const query = useQuery({
    queryKey: ["chain-session", sessionId],
    queryFn: () => chain.resume(sessionId),
    refetchOnWindowFocus: false,
  });
  if (query.isPending) return <Skeleton className="learning-skeleton" />;
  if (query.isError)
    return (
      <LearningError error={query.error} retry={() => void query.refetch()} />
    );
  return <ChainRound key={sessionId} initial={query.data} />;
}

type Draft = {
  links: LinkPair[];
  process: string | null;
  prediction: string | null;
};

function ChainRound({ initial }: { initial: ChainSession }) {
  const [game, setGame] = useState(initial);
  const [draft, setDraft] = useState<Draft>({
    links: initial.links,
    process: initial.process,
    prediction: initial.prediction ?? null,
  });
  const [history, setHistory] = useState<Draft[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [feedback, setFeedback] = useState(initial.feedback);
  const [leave, setLeave] = useState(false);
  const [runVersion, setRunVersion] = useState(0);
  const heading = useRef<HTMLHeadingElement>(null);
  const client = useQueryClient();
  const navigate = useNavigate();
  const run = useMutation({
    mutationFn: () =>
      chain.run(game.id, draft.links, draft.process, draft.prediction),
    onSuccess: (next) => {
      setGame(next);
      setFeedback(next.feedback);
      setRunVersion((v) => v + 1);
      client.setQueryData(["chain-session", game.id], next);
      if (next.result) {
        void client.invalidateQueries({ queryKey: ["chain-journey"] });
        void client.invalidateQueries({ queryKey: ["progress"] });
        heading.current?.focus({ preventScroll: true });
      }
    },
  });
  const next = useMutation({
    mutationFn: chain.start,
    onSuccess: (data) => navigate(`/games/chain/${data.id}`),
  });
  const completed = game.status === "completed";
  const edit = (value: Draft) => {
    if (completed || run.isPending) return;
    setHistory((h) => [...h, draft]);
    setDraft(value);
    setFeedback(null);
    run.reset();
  };
  const connect = (from: string, to: string) => {
    if (from === to) return;
    const exists = draft.links.some(([a, b]) => a === from && b === to);
    if (!exists) edit({ ...draft, links: [...draft.links, [from, to]] });
    setSelected(null);
  };
  const undo = () => {
    if (!history.length) return;
    setDraft(history[history.length - 1]);
    setHistory((h) => h.slice(0, -1));
    setFeedback(null);
    setSelected(null);
    run.reset();
  };
  useEffect(() => {
    heading.current?.focus({ preventScroll: true });
  }, []);
  useEffect(() => {
    // Expose only rendered board information; the server retains the solution.
    const read = () =>
      JSON.stringify({
        mode: completed ? "complete" : "building",
        level: game.level_id,
        coordinates: "SVG origin top-left, x right, y down",
        nodes: game.nodes.map((n) => ({ id: n.id, label: n.label })),
        links: draft.links,
        process: draft.process,
        prediction: draft.prediction,
        selected,
        feedback: feedback?.message ?? null,
      });
    const target = window as Window & { render_game_to_text?: () => string };
    target.render_game_to_text = read;
    return () => {
      delete target.render_game_to_text;
    };
  }, [game, draft, selected, feedback, completed]);
  if (game.status === "abandoned")
    return (
      <div className="learning-empty">
        <h2>This round is closed.</h2>
        <Link to="/games" className="button button-primary">
          Back to games
        </Link>
      </div>
    );
  const levelOrder = ["spark", "build", "oxygen", "repair", "mastery"];
  const index = levelOrder.indexOf(game.level_id);
  return (
    <div
      data-motion-revision={runVersion}
      className={`chain-play ${game.mode === "place" ? "play-placement" : ""} ${completed ? "play-complete" : ""}`}
      data-motion={
        completed && runVersion === 0
          ? "complete"
          : run.isPending
            ? "running"
            : feedback
              ? feedback.correct
                ? "success"
                : "retry"
              : selected
                ? "connecting"
                : "idle"
      }
    >
      <div className="chain-topbar">
        <button
          className="text-button"
          aria-label="Leave puzzle"
          onClick={() => setLeave(!leave)}
        >
          ← Back to games
        </button>
        <strong>Chain Reaction</strong>
        <div className="chain-steps" aria-label={`Challenge ${index + 1} of 5`}>
          {levelOrder.map((id, i) => (
            <i
              key={id}
              className={
                i < index || (completed && i === index)
                  ? "step-done"
                  : i === index
                    ? "step-current"
                    : ""
              }
            />
          ))}
          <strong>{index + 1} / 5</strong>
        </div>
      </div>
      {leave && (
        <div className="inline-confirm">
          <span>
            Return to Games? Connections from your last run stay saved.
          </span>
          <Link className="button button-secondary" to="/games">
            Return to games
          </Link>
          <Button variant="ghost" onClick={() => setLeave(false)}>
            Keep playing
          </Button>
        </div>
      )}
      <header className="chain-title">
        <span className="eyebrow">{game.title}</span>
        <h2 ref={heading} tabIndex={-1}>
          {completed ? "It works!" : game.goal}
        </h2>
        {completed && (
          <span className="chain-xp">+{game.result?.xp_earned} XP</span>
        )}
      </header>
      {game.prediction_prompt && !completed && (
        <p className="chain-forecast" id="prediction-prompt">
          <ArenaIcon name="bolt" size={23} />
          <span>{game.prediction_prompt}</span>
        </p>
      )}
      <div
        key={runVersion}
        className={`board-run ${feedback ? (feedback.correct ? (runVersion ? "run-success" : "") : "run-failed") : ""}`}
      >
        <ChainBoard
          nodes={game.nodes}
          links={draft.links}
          process={draft.process}
          placement={game.mode === "place"}
          prediction={draft.prediction}
          predictionOptions={completed ? [] : (game.prediction_options ?? [])}
          onPredict={(prediction) =>
            edit({
              ...draft,
              prediction: draft.prediction === prediction ? null : prediction,
            })
          }
          onPlace={(process) => edit({ ...draft, process })}
          selected={selected}
          onSelect={setSelected}
          onConnect={connect}
          onRemove={(i) =>
            edit({ ...draft, links: draft.links.filter((_, j) => i !== j) })
          }
          feedback={feedback}
          locked={completed || run.isPending}
        />
      </div>
      {run.isError && (
        <LearningError error={run.error} retry={() => run.mutate()} />
      )}
      {next.isError && <LearningError error={next.error} />}
      {feedback &&
        (feedback.correct ? (
          <details className="chain-explanation">
            <summary>Why it works</summary>
            <p>{feedback.message}</p>
          </details>
        ) : (
          <div className="chain-feedback incorrect" role="status">
            <span className="feedback-mark" aria-hidden="true">
              ↻
            </span>
            <div>
              <strong>Not quite. Try a different route.</strong>
              <p>{feedback.message}</p>
            </div>
          </div>
        ))}
      <footer className="chain-controls">
        {game.mode === "place" && !completed && (
          <div className="process-tray" aria-label="Choose a process">
            {game.choices.map((choice) => (
              <button
                key={choice.id}
                aria-pressed={draft.process === choice.id}
                draggable={!run.isPending}
                onDragStart={(event) =>
                  event.dataTransfer.setData(
                    "application/edusphere-process",
                    choice.id,
                  )
                }
                disabled={run.isPending}
                onClick={() =>
                  edit({
                    ...draft,
                    process: draft.process === choice.id ? null : choice.id,
                  })
                }
              >
                <BiologyArt
                  kind={choice.id === "digestion" ? "digestion" : choice.kind}
                  size={44}
                />
                <span>{choice.label}</span>
              </button>
            ))}
          </div>
        )}
        <div className="chain-hint">
          {completed ? (
            <BiologyArt
              kind={index === 1 ? "molecule" : "chloroplast"}
              size={68}
            />
          ) : (
            <ArenaIcon name="paths" size={20} />
          )}
          <span>
            {completed
              ? [
                  "Build the pathway",
                  "What if oxygen runs out?",
                  "Can you find the fault?",
                  "Build it from the beginning",
                  "Chapter complete.",
                ][index]
              : game.mode === "place"
                ? "Connect the missing step"
                : game.hint}
          </span>
        </div>
        <div>
          <a
            className="chain-source"
            href={game.source.url}
            target="_blank"
            rel="noreferrer"
            aria-label={`Read source: ${game.source.title}`}
            title={game.source.title}
          >
            <ArenaIcon name="library" size={23} />
            {completed && <span>Source Book</span>}
          </a>
          {!completed && (
            <button
              className="chain-undo"
              disabled={!history.length || run.isPending}
              onClick={undo}
              aria-label="Undo last move"
            >
              <span aria-hidden="true">↶</span>
            </button>
          )}
          {completed ? (
            index < 4 ? (
              <Button
                loading={next.isPending}
                aria-label="Next challenge"
                onClick={() => next.mutate(levelOrder[index + 1])}
              >
                TRY IT
              </Button>
            ) : (
              <Link className="button button-primary" to="/games">
                Chapter complete
                <span aria-hidden="true">✓</span>
              </Link>
            )
          ) : (
            <Button
              loading={run.isPending}
              disabled={
                run.isPending ||
                (game.mode === "place" && !draft.process) ||
                (Boolean(game.prediction_prompt) && !draft.prediction)
              }
              onClick={() => {
                setSelected(null);
                run.mutate();
              }}
            >
              <ArenaIcon name="play" size={19} />
              RUN
            </Button>
          )}
        </div>
      </footer>
    </div>
  );
}
