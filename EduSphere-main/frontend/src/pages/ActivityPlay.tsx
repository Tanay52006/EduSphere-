import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  activities,
  mechanicNames,
  type ActivityDraft,
  type ActivitySession,
} from "../lib/activities";
import { ActivityBoards } from "../components/ActivityBoards";
import { ArenaIcon } from "../components/ArenaIcon";
import { LearningError } from "../components/LearningUI";
import { Button, Skeleton } from "../components/ui";

export function ActivityPlay({ sessionId }: { sessionId: string }) {
  const query = useQuery({
    queryKey: ["activity-session", sessionId],
    queryFn: () => activities.resume(sessionId),
    refetchOnWindowFocus: false,
  });
  if (query.isPending) return <Skeleton className="learning-skeleton" />;
  if (query.isError)
    return (
      <LearningError error={query.error} retry={() => void query.refetch()} />
    );
  return <ActivityRound key={sessionId} initial={query.data} />;
}

function ActivityRound({ initial }: { initial: ActivitySession }) {
  const [game, setGame] = useState(initial);
  const [draft, setDraft] = useState(initial.draft);
  const [history, setHistory] = useState<ActivityDraft[]>([]);
  const [feedback, setFeedback] = useState(initial.feedback);
  const [leave, setLeave] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const client = useQueryClient();
  const completed = game.status === "completed";
  const run = useMutation({
    mutationFn: () => activities.run(game.id, draft),
    onSuccess: (next) => {
      setGame(next);
      setFeedback(next.feedback);
      client.setQueryData(["activity-session", game.id], next);
      if (next.result) {
        void client.invalidateQueries({ queryKey: ["progress"] });
        heading.current?.focus({ preventScroll: true });
      }
    },
  });
  const locked = completed || run.isPending || game.status !== "open";
  const edit = (value: ActivityDraft) => {
    if (locked) return;
    setHistory((old) => [...old, draft]);
    setDraft(value);
    setFeedback(null);
    run.reset();
  };
  const undo = () => {
    if (locked || !history.length) return;
    setDraft(history[history.length - 1]);
    setHistory((old) => old.slice(0, -1));
    setFeedback(null);
    run.reset();
  };
  useEffect(() => {
    heading.current?.focus({ preventScroll: true });
  }, []);
  useEffect(() => {
    const target = window as Window & { render_game_to_text?: () => string };
    target.render_game_to_text = () =>
      JSON.stringify({
        mode: completed ? "complete" : "building",
        mechanic: game.activity.mechanic,
        title: game.activity.title,
        items: game.activity.items,
        draft,
        feedback: feedback?.message ?? null,
      });
    return () => {
      delete target.render_game_to_text;
    };
  }, [game, draft, feedback, completed]);
  const ready =
    game.activity.mechanic === "sort"
      ? Object.keys(draft.assignments).length === game.activity.items.length
      : game.activity.mechanic === "connections"
        ? draft.links.length > 0
        : true;
  return (
    <div className="chain-play activity-play">
      <div className="chain-topbar">
        <button
          className="text-button"
          aria-label="Leave activity"
          onClick={() => setLeave(!leave)}
        >
          ← Back to games
        </button>
        <strong>{mechanicNames[game.activity.mechanic]}</strong>
        <span className="activity-attempts">
          {game.attempts
            ? `${game.attempts} checked`
            : "Untimed · Free retries"}
        </span>
      </div>
      {leave && (
        <div className="inline-confirm">
          <span>
            Your last checked arrangement is saved. Unchecked moves stay in this
            tab.
          </span>
          <Link className="button button-secondary" to="/games">
            Return to games
          </Link>
          <Button variant="ghost" onClick={() => setLeave(false)}>
            Keep playing
          </Button>
        </div>
      )}
      <header className="activity-title">
        <span className="eyebrow">
          {game.activity.subject} · {mechanicNames[game.activity.mechanic]}
        </span>
        <h2 ref={heading} tabIndex={-1}>
          {completed ? "You figured it out." : game.activity.title}
        </h2>
        <p>{completed ? game.result?.explanation : game.activity.goal}</p>
        {completed && (
          <span className="chain-xp">+{game.result?.xp_earned} XP</span>
        )}
      </header>
      {game.preview && (
        <p className="activity-preview-note">
          Development preview · Built from explicit source patterns. Review the
          cited page.
        </p>
      )}
      <ActivityBoards
        game={game}
        draft={draft}
        edit={edit}
        locked={locked}
        feedback={feedback}
      />
      {feedback && !completed && (
        <div className="chain-feedback" role="status">
          <ArenaIcon name="paths" size={22} />
          <div>
            <strong>Take another look</strong>
            <p>{feedback.message}</p>
          </div>
        </div>
      )}
      {run.isError && (
        <LearningError error={run.error} retry={() => run.mutate()} />
      )}
      {game.status === "abandoned" && (
        <p role="status">
          This round is closed. Return to Games to start a fresh one.
        </p>
      )}
      <footer className="chain-controls">
        <details className="activity-source">
          <summary>
            <ArenaIcon name="library" size={18} /> Source & approach
          </summary>
          <p>{game.activity.why_fit}</p>
          {game.sources.map((source) => (
            <a
              key={source.url}
              href={source.url}
              target="_blank"
              rel="noreferrer"
            >
              {source.title} ↗
            </a>
          ))}
        </details>
        <div>
          {!completed && (
            <button
              className="chain-undo"
              disabled={locked || !history.length}
              onClick={undo}
              aria-label="Undo last move"
            >
              ↶
            </button>
          )}
          {completed ? (
            <Link className="button button-primary" to="/games">
              More challenges <ArenaIcon name="arrow" size={18} />
            </Link>
          ) : (
            <Button
              loading={run.isPending}
              disabled={locked || !ready}
              onClick={() => run.mutate()}
            >
              <ArenaIcon name="play" size={18} />
              {game.activity.mechanic === "connections"
                ? "Run system"
                : "Check solution"}
            </Button>
          )}
        </div>
      </footer>
    </div>
  );
}
