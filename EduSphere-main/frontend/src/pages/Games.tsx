import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Button, Skeleton } from "../components/ui";
import { LearningError, ProgressStrip } from "../components/LearningUI";
import { api } from "../lib/api";
import { learning, type GameKind } from "../lib/learning";
import { QuestionBank } from "./QuestionBank";
import { ArenaArt } from "../components/ArenaArt";
import { ArenaIcon } from "../components/ArenaIcon";
import { ChainChapter } from "../components/ChainChapter";
import { ActivityStudio } from "../components/ActivityStudio";

export function Games({ bankView = false }: { bankView?: boolean }) {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const documents = useQuery({
    queryKey: ["documents"],
    queryFn: api.documents,
  });
  const ready = documents.data?.filter((doc) => doc.status === "ready") ?? [];
  const documentId = params.get("document") ?? ready[0]?.id ?? "";
  const bank = useQuery({
    queryKey: ["questions", documentId],
    queryFn: () => learning.bank(documentId),
    enabled: Boolean(documentId),
    retry: false,
  });
  const start = useMutation({
    mutationFn: (game: GameKind) => learning.start(documentId, game),
    onSuccess: (session) => navigate(`/games/play/${session.id}`),
  });
  const valid =
    bank.data?.questions.filter((q) => q.validated && !q.flagged) ?? [];
  const quizCount = valid.filter((q) => q.kind === "MCQ").length;
  const matchCount = valid.filter((q) => q.kind === "MATCH").length;
  const suffix = documentId ? `?document=${documentId}` : "";

  return (
    <div className="learning-content">
      <section className="learning-heading arena-heading">
        <div>
          <p className="eyebrow">Your study arena</p>
          <h2>{bankView ? "Question bank" : "Choose your game"}</h2>
        </div>
        {!bankView && <ProgressStrip />}
      </section>
      {!bankView && <ChainChapter />}
      <div className="workspace-toolbar">
        <nav className="workspace-tabs" aria-label="Learning workspace">
          <Link
            className={!bankView ? "selected" : ""}
            aria-current={!bankView ? "page" : undefined}
            to={`/games${suffix}`}
          >
            Play & practice
          </Link>
          <Link
            className={bankView ? "selected" : ""}
            aria-current={bankView ? "page" : undefined}
            to={`/questions${suffix}`}
          >
            Question bank <span>{bank.data?.questions.length ?? "—"}</span>
          </Link>
        </nav>
        {ready.length > 0 && (
          <label className="material-select">
            <span>Study material</span>
            <select
              aria-label="Choose study material"
              value={documentId}
              onChange={(event) => setParams({ document: event.target.value })}
            >
              {ready.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.original_filename}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>
      {!bankView && <ActivityStudio key={documentId} documentId={documentId} />}
      {documents.isPending ? (
        <Skeleton className="learning-skeleton" />
      ) : documents.isError ? (
        <LearningError
          error={documents.error}
          retry={() => void documents.refetch()}
        />
      ) : !documentId ? (
        <section className="learning-empty">
          <span className="empty-orbit" aria-hidden="true">
            <ArenaIcon name="library" size={48} />
          </span>
          <h3>Add material to unlock games</h3>
          <p>
            Upload a PDF, let it finish processing, then turn it into questions
            and games.
          </p>
          <Link className="button button-primary" to="/library">
            Add your first material <span aria-hidden="true">↗</span>
          </Link>
        </section>
      ) : bank.isPending ? (
        <Skeleton className="learning-skeleton" />
      ) : bank.isError ? (
        <LearningError error={bank.error} retry={() => void bank.refetch()} />
      ) : bankView ? (
        <QuestionBank
          key={documentId}
          documentId={documentId}
          bank={bank.data!}
        />
      ) : (
        <>
          {start.isError && <LearningError error={start.error} />}
          <section className="game-catalog" aria-label="Choose a game">
            <article className="game-tile tile-blitz">
              <ArenaArt />
              <div className="game-tile-copy">
                <div className="game-title-row">
                  <h3>Quiz Blitz</h3>
                  <ArenaIcon name="bolt" />
                </div>
                <p>Beat the clock. Keep your lives.</p>
                <div className="game-specs">
                  <span>
                    <ArenaIcon name="target" size={15} />
                    10 questions
                  </span>
                  <span>
                    <ArenaIcon name="heart" size={15} />3 lives
                  </span>
                  <span>
                    <ArenaIcon name="clock" size={15} />
                    30s
                  </span>
                </div>
                <Button
                  loading={start.isPending && start.variables === "quiz_blitz"}
                  disabled={quizCount < 10 || start.isPending}
                  onClick={() => start.mutate("quiz_blitz")}
                >
                  <ArenaIcon name="play" size={17} />
                  Play Quiz Blitz
                </Button>
                {quizCount < 10 && (
                  <small className="game-requirement">
                    Needs 10 validated multiple-choice questions · {quizCount}{" "}
                    ready
                  </small>
                )}
              </div>
            </article>
            <article className="game-tile tile-memory">
              <ArenaArt memory />
              <div className="game-tile-copy">
                <div className="game-title-row">
                  <h3>Memory Match</h3>
                  <ArenaIcon name="cards" />
                </div>
                <p>Flip the cards. Connect each pair.</p>
                <div className="game-specs">
                  <span>
                    <ArenaIcon name="cards" size={15} />6 pairs
                  </span>
                  <span>
                    <ArenaIcon name="clock" size={15} />
                    Untimed
                  </span>
                </div>
                <Button
                  variant="secondary"
                  loading={
                    start.isPending && start.variables === "memory_match"
                  }
                  disabled={matchCount < 6 || start.isPending}
                  onClick={() => start.mutate("memory_match")}
                >
                  <ArenaIcon name="play" size={17} />
                  Play Memory Match
                </Button>
                {matchCount < 6 && (
                  <small className="game-requirement">
                    Needs 6 validated definition pairs · {matchCount} ready
                  </small>
                )}
              </div>
            </article>
          </section>
          <div className="bank-invitation">
            <span className="bank-invitation-mark" aria-hidden="true">
              <ArenaIcon name="library" />
            </span>
            <div>
              <strong>
                {valid.length
                  ? `${valid.length} questions ready`
                  : "Unlock these games"}
              </strong>
              <p>
                {valid.length
                  ? "Review or add to your question bank."
                  : "Generate questions from your selected material."}
              </p>
            </div>
            <Link className="text-button" to={`/questions${suffix}`}>
              {valid.length ? "Explore your bank" : "Create question bank"} ↗
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
