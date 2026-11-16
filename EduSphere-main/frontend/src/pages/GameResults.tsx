import { useMutation } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Button } from "../components/ui";
import { ArenaIcon } from "../components/ArenaIcon";
import { LearningError, Sources } from "../components/LearningUI";
import { learning, type GameResult } from "../lib/learning";

export function GameResults({ result }: { result: GameResult }) {
  const flag = useMutation({ mutationFn: learning.flag });
  const minutes = Math.floor(result.duration_s / 60);
  return (
    <div className="results-content">
      <Link className="text-button" to="/games">
        ← Back to the arcade
      </Link>
      <section className="results-hero">
        <span className="result-emblem">
          <ArenaIcon name="trophy" size={36} />
        </span>
        <p className="eyebrow">
          {result.game === "quiz_blitz" ? "Quiz Blitz" : "Memory Match"} ·
          Session complete
        </p>
        <h2>Round complete</h2>
        <p>Your results are saved.</p>
        <div className="earned-xp">
          +{result.xp_earned}
          <span>XP earned</span>
        </div>
      </section>
      <div className="result-metrics">
        <div>
          <strong>
            {result.correct}
            <em> / {result.total}</em>
          </strong>
          <span>
            {result.game === "quiz_blitz"
              ? "Correct answers"
              : "Pairs connected"}
          </span>
        </div>
        <div>
          <strong>
            {result.accuracy}
            <em>%</em>
          </strong>
          <span>
            {result.game === "quiz_blitz" ? "Accuracy" : "Match efficiency"}
          </span>
        </div>
        <div>
          <strong>
            {minutes}:{String(result.duration_s % 60).padStart(2, "0")}
          </strong>
          <span>Time spent learning</span>
        </div>
      </div>
      <div className="result-progress">
        <div>
          <span className="eyebrow">
            Level {result.progress.level} · {result.progress.tier}
          </span>
          <strong>
            {result.progress.level_xp} / {result.progress.level_target} XP
          </strong>
          <div className="round-track">
            <span
              style={{
                transform: `scaleX(${result.progress.level_xp / result.progress.level_target})`,
              }}
            />
          </div>
        </div>
        <span>
          <ArenaIcon name="flame" size={18} /> {result.progress.streak} day
          streak
        </span>
      </div>
      <div className="result-actions">
        <Link className="button button-primary" to="/games">
          Play again
        </Link>
        <Link className="button button-secondary" to="/progress">
          See your progress
        </Link>
      </div>
      {result.review.length > 0 && (
        <section className="result-review">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Review</p>
              <h3>Round review</h3>
            </div>
            <span>Every answer, with its source</span>
          </div>
          {flag.isError && <LearningError error={flag.error} />}
          {flag.isSuccess && (
            <p role="status" className="generation-status">
              Question flagged. It will stay out of future games.
            </p>
          )}
          {result.review.map((q, i) => (
            <details key={q.question_id}>
              <summary>
                <span className={q.correct ? "review-right" : "review-wrong"}>
                  {q.correct ? "✓" : "↻"}
                </span>
                <strong>
                  {i + 1}. {q.prompt}
                </strong>
                <span aria-hidden="true">＋</span>
              </summary>
              <div className="review-answer">
                <strong>{q.answer}</strong>
                <p>{q.explanation}</p>
                {q.sources && <Sources sources={q.sources} />}
                <Button
                  variant="ghost"
                  disabled={flag.isPending}
                  onClick={() => flag.mutate(q.question_id)}
                >
                  ⚑ Flag this question
                </Button>
              </div>
            </details>
          ))}
        </section>
      )}
    </div>
  );
}
