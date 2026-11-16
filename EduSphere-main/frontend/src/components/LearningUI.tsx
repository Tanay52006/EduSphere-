import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Button, Skeleton } from "./ui";
import { ArenaIcon } from "./ArenaIcon";
import { learning, type Source } from "../lib/learning";

export function LearningError({
  error,
  retry,
}: {
  error: unknown;
  retry?: () => void;
}) {
  return (
    <div className="learning-error" role="alert">
      <span>
        {error instanceof Error
          ? error.message
          : "Something went wrong. Please try again."}
      </span>
      {retry && (
        <Button variant="ghost" onClick={retry}>
          Try again
        </Button>
      )}
    </div>
  );
}

export function Sources({ sources }: { sources: Source[] }) {
  return (
    <div className="source-links">
      {sources.map((source) => (
        <a
          key={source.chunk_id}
          href={source.url}
          target="_blank"
          rel="noreferrer"
        >
          ↗ Source · p. {source.page_start}
          {source.page_end !== source.page_start ? `–${source.page_end}` : ""}
        </a>
      ))}
    </div>
  );
}

export function ProgressStrip() {
  const progress = useQuery({
    queryKey: ["progress"],
    queryFn: learning.progress,
    retry: false,
  });
  if (progress.isPending)
    return <Skeleton className="progress-strip-skeleton" />;
  if (progress.isError)
    return (
      <LearningError
        error={progress.error}
        retry={() => void progress.refetch()}
      />
    );
  const p = progress.data;
  return (
    <Link
      to="/progress"
      className="learning-strip"
      aria-label={`Your progress: ${p.total_xp} XP, ${p.streak} day streak`}
    >
      <span className="strip-level">{p.level}</span>
      <span>
        <strong>Level {p.level}</strong>
        <small>{p.total_xp.toLocaleString()} XP</small>
      </span>
      <span className="strip-divider" />
      <span className="strip-streak">
        <ArenaIcon name="flame" size={23} />
        <span>
          <strong>
            {p.streak} <em>day{p.streak !== 1 ? "s" : ""}</em>
          </strong>
          <small>streak</small>
        </span>
      </span>
      <span className="strip-arrow" aria-hidden="true">
        ↗
      </span>
    </Link>
  );
}
