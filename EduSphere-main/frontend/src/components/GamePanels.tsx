import type { RefObject } from "react";
import { Button } from "./ui";
import { ArenaIcon } from "./ArenaIcon";
import { Sources } from "./LearningUI";
import type { PlaySession } from "../lib/learning";

export function MemoryBoard({
  session,
  heading,
  busy,
  onFlip,
}: {
  session: PlaySession;
  heading: RefObject<HTMLHeadingElement>;
  busy: boolean;
  onFlip: (id: string) => void;
}) {
  const feedback = session.feedback;
  return (
    <>
      <div className="board-heading">
        <div>
          <h2 ref={heading} tabIndex={-1}>
            Memory Match
          </h2>
          <p>Match each term to its definition.</p>
        </div>
        <span className="board-mark">
          <ArenaIcon name="cards" size={28} />
        </span>
      </div>
      <div className="memory-board" aria-label="Memory Match board">
        {session.cards?.map((card, i) => (
          <button
            key={card.id}
            className={`memory-card ${card.text ? "revealed" : ""} ${card.matched ? "matched" : ""}`}
            aria-disabled={
              busy ||
              card.matched ||
              (card.text !== null &&
                session.cards?.filter((c) => c.text && !c.matched).length === 1)
            }
            aria-label={
              card.matched
                ? `Matched: ${card.text}`
                : (card.text ?? `Turn over card ${i + 1}`)
            }
            onClick={() => {
              const singleRevealed =
                card.text !== null &&
                session.cards?.filter((c) => c.text && !c.matched).length === 1;
              if (!busy && !card.matched && !singleRevealed) onFlip(card.id);
            }}
          >
            <span className="memory-card-back" aria-hidden="true">
              <span className="deck-mark" />
            </span>
            <span className="memory-card-front">
              {card.text}
              {card.matched && <small>✓ Connected</small>}
            </span>
          </button>
        ))}
      </div>
      <p className="memory-feedback" role="status">
        {feedback
          ? feedback.correct
            ? "Pair matched."
            : "No match. Try another pair."
          : "Select two cards."}
      </p>
      {feedback?.sources && <Sources sources={feedback.sources} />}
    </>
  );
}

export function QuizFeedback({
  session,
  heading,
  busy,
  onNext,
}: {
  session: PlaySession;
  heading: RefObject<HTMLHeadingElement>;
  busy: boolean;
  onNext: () => void;
}) {
  const feedback = session.feedback;
  if (!feedback) return null;
  return (
    <section
      className={`answer-feedback ${feedback.correct ? "feedback-correct" : "feedback-wrong"}`}
    >
      <span className="feedback-symbol" aria-hidden="true">
        <ArenaIcon name={feedback.correct ? "check" : "paths"} size={25} />
      </span>
      <p className="eyebrow">
        {feedback.timed_out
          ? "Time for another try"
          : feedback.correct
            ? "Correct answer"
            : "Answer revealed"}
      </p>
      <h2 ref={heading} tabIndex={-1}>
        {feedback.correct ? "Correct" : "Keep going"}
      </h2>
      <strong>{feedback.answer}</strong>
      <p>{feedback.explanation}</p>
      {feedback.sources && <Sources sources={feedback.sources} />}
      <div className="feedback-bottom">
        <span>
          {session.combo > 1 ? `${session.combo} correct in a row.` : ""}
        </span>
        <Button loading={busy} onClick={() => onNext()}>
          Next question →
        </Button>
      </div>
    </section>
  );
}
