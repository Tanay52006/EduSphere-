import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { Button, Skeleton } from "../components/ui";
import { LearningError } from "../components/LearningUI";
import { learning, type PlaySession } from "../lib/learning";
import { MemoryBoard, QuizFeedback } from "../components/GamePanels";
import { GameResults } from "./GameResults";
import { ArenaIcon } from "../components/ArenaIcon";

export function GamePlay({ sessionId }: { sessionId: string }) {
  const client = useQueryClient();
  const navigate = useNavigate();
  const [now, setNow] = useState(Date.now());
  const [leaving, setLeaving] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const timedOut = useRef("");
  const query = useQuery({
    queryKey: ["game-session", sessionId],
    queryFn: () => learning.resume(sessionId),
    retry: false,
    refetchOnWindowFocus: false,
  });
  const session = query.data;
  const update = (next: PlaySession) =>
    client.setQueryData(["game-session", sessionId], next);
  const action = useMutation({
    mutationFn: (run: () => Promise<PlaySession>) => run(),
    onSuccess: update,
  });
  const finish = useMutation({
    mutationFn: () => learning.submit(sessionId),
    onSuccess: (result) => {
      if (session) update({ ...session, status: "completed", result });
      void client.invalidateQueries({ queryKey: ["progress"] });
    },
  });
  const abandon = useMutation({
    mutationFn: () => learning.abandon(sessionId),
    onSuccess: () => navigate("/games"),
  });
  const seconds = Math.max(0, Math.ceil((session?.deadline ?? 0) - now / 1000));
  const busy = action.isPending || finish.isPending || abandon.isPending;

  useEffect(() => {
    const interval = setInterval(() => setNow(Date.now()), 250);
    return () => clearInterval(interval);
  }, []);
  useEffect(() => {
    heading.current?.focus({ preventScroll: true });
  }, [session?.question?.id, session?.index, session?.status]);
  useEffect(() => {
    if (session?.game !== "quiz_blitz" || session.status !== "open") return;
    const onVisibility = () => {
      if (document.hidden) action.mutate(() => learning.clock(sessionId, true));
    };
    document.addEventListener("visibilitychange", onVisibility);
    return () => document.removeEventListener("visibilitychange", onVisibility);
    // The listener always uses this session's stable mutation function.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, session?.game, session?.status]);
  useEffect(() => {
    const q = session?.question;
    if (
      !q ||
      session?.status !== "open" ||
      session.paused ||
      seconds > 0 ||
      busy ||
      timedOut.current === q.id ||
      document.hidden
    )
      return;
    timedOut.current = q.id;
    action.mutate(() => learning.answer(sessionId, q.id, ""));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session, seconds, busy, sessionId]);

  if (query.isPending) return <Skeleton className="play-loading" />;
  if (query.isError)
    return (
      <div className="learning-content">
        <LearningError error={query.error} retry={() => void query.refetch()} />
        <Link className="text-button" to="/games">
          ← Back to games
        </Link>
      </div>
    );
  if (!session) return null;
  if (session.result) return <GameResults result={session.result} />;
  if (session.status === "abandoned")
    return (
      <div className="learning-empty">
        <h2>This session is closed.</h2>
        <Link className="button button-primary" to="/games">
          Choose another challenge
        </Link>
      </div>
    );
  const memory = session.game === "memory_match";
  const feedback = session.feedback;
  const q = session.question;
  return (
    <div
      className={`play-content ${memory ? "playing-memory" : "playing-quiz"}`}
    >
      <div className="play-topline">
        <button className="text-button" onClick={() => setLeaving(!leaving)}>
          ← Leave session
        </button>
        <span className="eyebrow">
          {memory ? "02 / Memory Match" : "01 / Quiz Blitz"}
        </span>
        <span className="play-live">● LET’S PLAY</span>
      </div>
      {leaving && (
        <div className="inline-confirm">
          <span>Leave this round? Your completed sessions stay saved.</span>
          <Button
            variant="secondary"
            loading={abandon.isPending}
            onClick={() => abandon.mutate()}
          >
            Leave round
          </Button>
          <Button variant="ghost" onClick={() => setLeaving(false)}>
            Keep playing
          </Button>
        </div>
      )}
      <div className="play-stats">
        <div>
          <small>{memory ? "Pairs found" : "Questions"}</small>
          <strong>
            {memory
              ? session.correct
              : Math.min(session.index + (q ? 1 : 0), session.total)}
            <span> / {session.total}</span>
          </strong>
        </div>
        <div>
          <small>{memory ? "Moves" : "Lives remaining"}</small>
          <strong>
            {memory ? (
              session.moves
            ) : (
              <span
                className="lives"
                aria-label={`${session.lives} lives remaining`}
              >
                {[0, 1, 2].map((i) => (
                  <i key={i} className={i < session.lives ? "" : "lost"}>
                    <ArenaIcon name="heart" size={19} />
                  </i>
                ))}
              </span>
            )}
          </strong>
        </div>
        <div>
          <small>{memory ? "Take your time" : "Your score"}</small>
          <strong>{memory ? "No rush" : session.score.toLocaleString()}</strong>
        </div>
      </div>
      <div
        className="round-track"
        role="progressbar"
        aria-label="Round progress"
        aria-valuemin={0}
        aria-valuemax={session.total}
        aria-valuenow={memory ? session.correct : session.index}
      >
        <span
          style={{
            transform: `scaleX(${(memory ? session.correct : session.index) / session.total})`,
          }}
        />
      </div>
      {action.isError && (
        <LearningError
          error={action.error}
          retry={() => {
            action.reset();
            void query.refetch();
          }}
        />
      )}
      {finish.isError && (
        <LearningError error={finish.error} retry={() => finish.mutate()} />
      )}
      {abandon.isError && <LearningError error={abandon.error} />}
      {session.status === "finished" ? (
        <section className="round-finished">
          <span className="finish-seal">
            <ArenaIcon name="trophy" size={36} />
          </span>
          <p className="eyebrow">Round complete</p>
          <h2 ref={heading} tabIndex={-1}>
            {session.lives === 0 ? "Round complete" : "Round complete"}
          </h2>
          <p>
            {memory
              ? `All ${session.total} connections found in ${session.moves} moves.`
              : `${session.correct} of ${session.total} questions answered correctly. `}
          </p>
          <Button loading={finish.isPending} onClick={() => finish.mutate()}>
            See results & collect XP <span aria-hidden="true">↗</span>
          </Button>
        </section>
      ) : memory ? (
        <MemoryBoard
          session={session}
          heading={heading}
          busy={busy}
          onFlip={(id) => action.mutate(() => learning.flip(sessionId, id))}
        />
      ) : feedback ? (
        <QuizFeedback
          session={session}
          heading={heading}
          busy={action.isPending}
          onNext={() => action.mutate(() => learning.next(sessionId))}
        />
      ) : q ? (
        <section className="quiz-question">
          <div className="question-topline">
            <span className="eyebrow">
              Question {String(session.index + 1).padStart(2, "0")}
            </span>
            <div
              className={`question-clock ${seconds <= 5 ? "clock-low" : ""}`}
            >
              <span role="timer" aria-label="Seconds remaining">
                {session.paused ? "Paused" : `${seconds}s`}
              </span>
              <button
                onClick={() =>
                  action.mutate(() =>
                    learning.clock(sessionId, !session.paused),
                  )
                }
                disabled={busy}
              >
                {session.paused ? "Resume" : "Pause"}
              </button>
            </div>
          </div>
          <h2 ref={heading} tabIndex={-1}>
            {q.prompt}
          </h2>
          {session.paused ? (
            <div className="pause-note">
              <p>Timer paused.</p>
              <Button
                loading={action.isPending}
                onClick={() =>
                  action.mutate(() => learning.clock(sessionId, false))
                }
              >
                Resume question
              </Button>
            </div>
          ) : (
            <div className="quiz-options" aria-label="Answer choices">
              {q.options.map((option, i) => (
                <button
                  key={option}
                  disabled={busy || seconds === 0}
                  onClick={() =>
                    action.mutate(() =>
                      learning.answer(sessionId, q.id, option),
                    )
                  }
                >
                  <span>{String.fromCharCode(65 + i)}</span>
                  <strong>{option}</strong>
                  <i aria-hidden="true">↗</i>
                </button>
              ))}
            </div>
          )}
          <p className="quiz-bottom-note">Select an answer.</p>
          {seconds === 0 && !busy && (
            <Button
              variant="secondary"
              onClick={() =>
                action.mutate(() => learning.answer(sessionId, q.id, ""))
              }
            >
              Continue after timeout
            </Button>
          )}
        </section>
      ) : null}
      <footer className="play-footer">
        <span></span>
        <span>EduSphere</span>
      </footer>
    </div>
  );
}
