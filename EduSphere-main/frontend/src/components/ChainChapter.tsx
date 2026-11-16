import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { chain } from "../lib/chain";
import { BiologyArt } from "./BiologyArt";
import { ArenaIcon } from "./ArenaIcon";
import { LearningError } from "./LearningUI";
import { Button, Skeleton } from "./ui";

export function ChainChapter() {
  const query = useQuery({
    queryKey: ["chain-journey"],
    queryFn: chain.journey,
  });
  const navigate = useNavigate();
  const start = useMutation({
    mutationFn: chain.start,
    onSuccess: (game) => navigate(`/games/chain/${game.id}`),
  });
  if (query.isPending) return <Skeleton className="chapter-loading" />;
  if (query.isError)
    return (
      <LearningError error={query.error} retry={() => void query.refetch()} />
    );
  const levels = query.data.levels;
  const completed = levels.filter((level) => level.completed).length;
  const active =
    levels.find((level) => level.unlocked && !level.completed) ?? levels[0];
  return (
    <section className="chain-chapter" aria-label="Chain Reaction chapter">
      <div className="chapter-preview" aria-hidden="true">
        <BiologyArt kind="chloroplast" size={72} />
        <span>→</span>
        <BiologyArt kind="battery" size={58} />
      </div>
      <div className="chapter-copy">
        <span className="eyebrow">Biology · Starter chapter</span>
        <h3>Chain Reaction</h3>
        <p>Build a system. Predict what changes. Find the fault.</p>
        <div className="chapter-stops" aria-label="Chapter challenges">
          {levels.map((level, index) => (
            <button
              key={level.id}
              disabled={!level.unlocked || start.isPending}
              className={
                level.completed
                  ? "chapter-stop-done"
                  : level.id === active.id
                    ? "chapter-stop-current"
                    : ""
              }
              onClick={() => start.mutate(level.id)}
              aria-label={`${level.completed ? "Replay" : level.unlocked ? "Play" : "Locked"}: ${level.title}`}
              title={level.title}
            >
              {level.completed ? (
                <ArenaIcon name="check" size={15} />
              ) : level.unlocked ? (
                index + 1
              ) : (
                <ArenaIcon name="lock" size={14} />
              )}
            </button>
          ))}
          <small>
            {completed} / {levels.length}
          </small>
        </div>
      </div>
      <div className="chapter-action">
        <Button
          loading={start.isPending}
          onClick={() => start.mutate(active.id)}
          aria-label="Play Chain Reaction"
        >
          <ArenaIcon name="play" size={18} />
          {completed === levels.length
            ? "Play again"
            : completed
              ? "Continue"
              : "Play"}
        </Button>
        <small>Untimed · Free retries</small>
      </div>
      {start.isError && <LearningError error={start.error} />}
    </section>
  );
}
