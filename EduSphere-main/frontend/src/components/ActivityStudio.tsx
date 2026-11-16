import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { activities, mechanicNames } from "../lib/activities";
import { Button, Skeleton } from "./ui";
import { ArenaIcon } from "./ArenaIcon";
import { LearningError } from "./LearningUI";

export function ActivityStudio({ documentId }: { documentId: string }) {
  const [subject, setSubject] = useState("All subjects");
  const [focus, setFocus] = useState("");
  const client = useQueryClient();
  const navigate = useNavigate();
  const catalog = useQuery({
    queryKey: ["activities"],
    queryFn: activities.catalog,
  });
  const start = useMutation({
    mutationFn: activities.start,
    onSuccess: (game) => navigate(`/games/activity/${game.id}`),
  });
  const generate = useMutation({
    mutationFn: () => activities.generate(documentId, focus),
    onSuccess: () => {
      setSubject("Your material");
      void client.invalidateQueries({ queryKey: ["activities"] });
    },
  });
  const all = catalog.data?.activities ?? [];
  const subjects = [
    "All subjects",
    ...new Set(all.filter((a) => !a.generated).map((a) => a.subject)),
    "Your material",
  ];
  const visible = all.filter((a) =>
    a.generated
      ? a.document_id === documentId &&
        (subject === "All subjects" || subject === "Your material")
      : subject === "All subjects" || a.subject === subject,
  );
  return (
    <section className="activity-studio" aria-label="Subject games">
      <div className="activity-section-heading">
        <div>
          <span className="eyebrow">
            Different subjects. Different ways to play.
          </span>
          <h3>Find your next challenge</h3>
        </div>
        <label className="material-select">
          <span>Explore</span>
          <select
            aria-label="Filter games by subject"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
          >
            {subjects.map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </label>
      </div>
      {catalog.isPending ? (
        <Skeleton className="activity-loading" />
      ) : catalog.isError ? (
        <LearningError
          error={catalog.error}
          retry={() => void catalog.refetch()}
        />
      ) : (
        <div className="subject-games">
          {visible.map((card) => (
            <article
              className={`subject-game mechanic-${card.mechanic}`}
              key={card.id}
            >
              <div className="subject-game-top">
                <span className="subject-token" aria-hidden="true">
                  {card.mechanic === "sequence"
                    ? "1 → 2"
                    : card.mechanic === "sort"
                      ? "A / B"
                      : "●—●"}
                </span>
                <span>
                  {card.generated
                    ? card.preview
                      ? "Development preview"
                      : "From your material"
                    : card.subject}
                </span>
              </div>
              <h4>{card.title}</h4>
              <p>{card.goal}</p>
              <div className="subject-game-bottom">
                <small>
                  {mechanicNames[card.mechanic]} · {card.size} pieces
                </small>
                <Button
                  variant="secondary"
                  loading={start.isPending && start.variables === card.id}
                  disabled={start.isPending}
                  onClick={() => start.mutate(card.id)}
                  aria-label={`Play ${card.title}`}
                >
                  <ArenaIcon name="play" size={15} />
                  Play
                </Button>
              </div>
            </article>
          ))}
        </div>
      )}
      {visible.length === 0 && !catalog.isPending && !catalog.isError && (
        <p className="activity-empty">
          Make a game from your selected material to start this collection.
        </p>
      )}
      {start.isError && <LearningError error={start.error} />}
      <form
        className="activity-generator"
        onSubmit={(event) => {
          event.preventDefault();
          if (documentId) generate.mutate();
        }}
      >
        <div>
          <ArenaIcon name="games" size={25} />
          <div>
            <h4>Make this material playable</h4>
            <p>
              A sequence, a sorting challenge or a system—chosen to fit your
              pages.
            </p>
          </div>
        </div>
        {documentId ? (
          <>
            <label>
              <span>
                Focus <small>optional</small>
              </span>
              <input
                value={focus}
                maxLength={160}
                onChange={(e) => setFocus(e.target.value)}
                placeholder="A process, chapter or concept…"
                autoComplete="off"
              />
            </label>
            <Button type="submit" loading={generate.isPending}>
              {generate.isPending ? "Building & checking…" : "Create a game"}
            </Button>
          </>
        ) : (
          <Link className="button button-secondary" to="/library">
            Add study material ↗
          </Link>
        )}
        {generate.isError && <LearningError error={generate.error} />}
        {catalog.data?.preview_mode && (
          <p className="generator-preview-note">
            Development mode: generation uses explicit source patterns. A
            configured AI provider enables broader topic selection.
          </p>
        )}
        {generate.isSuccess && (
          <p role="status">
            {generate.data.preview
              ? "Development preview ready. Open the game and review its source."
              : "Your source-checked game is ready above."}
          </p>
        )}
      </form>
    </section>
  );
}
