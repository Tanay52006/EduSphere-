import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Button, Input } from "../components/ui";
import { LearningError, Sources } from "../components/LearningUI";
import { learning, type Bank, type StudyQuestion } from "../lib/learning";

function QuestionRow({
  question,
  index,
  refresh,
}: {
  question: StudyQuestion;
  index: number;
  refresh: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [prompt, setPrompt] = useState(question.prompt);
  const [deleting, setDeleting] = useState(false);
  const action = useMutation({
    mutationFn: async (kind: "edit" | "flag" | "delete") => {
      if (kind === "edit") await learning.edit(question.id, prompt);
      else if (kind === "flag") await learning.flag(question.id);
      else await learning.remove(question.id);
    },
    onSuccess: () => {
      setEditing(false);
      refresh();
    },
  });
  return (
    <article
      className={`bank-question ${question.flagged ? "is-flagged" : ""}`}
    >
      <span className="question-number">
        {String(index + 1).padStart(2, "0")}
      </span>
      <div className="question-body">
        <div className="question-meta">
          <span>
            {question.kind === "MCQ" ? "Multiple choice" : "Definition pair"}
          </span>
          <span
            className={`question-state ${question.validated && !question.flagged ? "is-validated" : ""}`}
          >
            {question.flagged
              ? "⚑ Flagged · excluded from games"
              : question.validated
                ? "✓ Source checked"
                : "Edited · excluded from games"}
          </span>
        </div>
        {editing ? (
          <form
            onSubmit={(event) => {
              event.preventDefault();
              action.mutate("edit");
            }}
          >
            <Input
              label="Question prompt"
              name={`prompt-${question.id}`}
              value={prompt}
              minLength={8}
              maxLength={600}
              onChange={(event) => setPrompt(event.target.value)}
              required
            />
            <p className="editing-note">
              Edits remove validation. This question stays out of games;
              generate a fresh source-checked version when ready.
            </p>
            <div className="inline-actions">
              <Button type="submit" loading={action.isPending}>
                Save prompt
              </Button>
              <Button
                variant="ghost"
                type="button"
                onClick={() => setEditing(false)}
              >
                Cancel
              </Button>
            </div>
          </form>
        ) : (
          <h3>{question.prompt}</h3>
        )}
        <details>
          <summary>
            Answer & explanation <span aria-hidden="true">＋</span>
          </summary>
          <div className="question-detail">
            {question.kind === "MCQ" && (
              <ul className="bank-options">
                {question.options.map((option, i) => (
                  <li
                    key={option}
                    className={
                      option === question.answer ? "correct-option" : ""
                    }
                  >
                    <span>{String.fromCharCode(65 + i)}</span>
                    {option}
                    {option === question.answer && <b>✓ Correct</b>}
                  </li>
                ))}
              </ul>
            )}
            {question.kind === "MATCH" && (
              <p className="definition-pair">
                <strong>{question.term}</strong>
                <span>↔</span>
                {question.definition}
              </p>
            )}
            <p>{question.explanation}</p>
            <Sources sources={question.sources} />
          </div>
        </details>
        <div className="question-actions">
          <button
            onClick={() => {
              setPrompt(question.prompt);
              setEditing(!editing);
            }}
            disabled={action.isPending}
          >
            Edit prompt
          </button>
          <button
            onClick={() => action.mutate("flag")}
            disabled={question.flagged || action.isPending}
          >
            ⚑ Flag question
          </button>
          <button
            onClick={() => setDeleting(!deleting)}
            disabled={action.isPending}
          >
            Remove
          </button>
        </div>
        {deleting && (
          <div className="inline-confirm">
            <span>Remove this question from your bank?</span>
            <Button
              variant="destructive"
              loading={action.isPending}
              onClick={() => action.mutate("delete")}
            >
              Remove question
            </Button>
            <Button variant="ghost" onClick={() => setDeleting(false)}>
              Keep it
            </Button>
          </div>
        )}
        {action.isError && <LearningError error={action.error} />}
      </div>
    </article>
  );
}

export function QuestionBank({
  documentId,
  bank,
}: {
  documentId: string;
  bank: Bank;
}) {
  const client = useQueryClient();
  const [filter, setFilter] = useState("all");
  const refresh = () => {
    void client.invalidateQueries({ queryKey: ["questions", documentId] });
  };
  const generation = useMutation({
    mutationFn: () => learning.generate(documentId),
    onSuccess: refresh,
  });
  const visible = bank.questions.filter(
    (q) => filter === "all" || q.kind === filter,
  );
  return (
    <section className="question-bank">
      <div className="bank-heading">
        <div>
          <p className="eyebrow">From reading to remembering</p>
          <h3>Your question collection</h3>
          <p>
            Every accepted question carries a source. Your judgment has the last
            word.
          </p>
        </div>
        <Button
          loading={generation.isPending}
          onClick={() => generation.mutate()}
        >
          {generation.isPending
            ? "Creating & checking…"
            : bank.questions.length
              ? "Generate more questions"
              : "Generate questions"}{" "}
          <span aria-hidden="true">＋</span>
        </Button>
      </div>
      {generation.isPending && (
        <div className="generation-status" role="status">
          <span className="generation-dot" />
          Reading your material, writing questions, and checking each answer
          against its source. This can take a minute.
        </div>
      )}
      {generation.isError && (
        <LearningError
          error={generation.error}
          retry={() => generation.mutate()}
        />
      )}
      {generation.isSuccess && (
        <p className="generation-status" role="status">
          ✓ {generation.data.added} new questions added.{" "}
          {generation.data.accepted} of {generation.data.generated} passed
          source validation.
        </p>
      )}
      {bank.quality && (
        <div className="quality-note">
          <span>
            ✓ {Math.round(bank.quality.pass_rate * 100)}% passed the latest
            validation
          </span>
          <span>
            {bank.quality.accepted} / {bank.quality.generated} accepted · target
            85%
          </span>
        </div>
      )}
      {bank.questions.length ? (
        <>
          <div className="bank-filters" aria-label="Filter questions">
            {[
              ["all", "All questions"],
              ["MCQ", "Multiple choice"],
              ["MATCH", "Definition pairs"],
            ].map(([value, label]) => (
              <button
                key={value}
                aria-pressed={filter === value}
                onClick={() => setFilter(value)}
              >
                {label}
                <span>
                  {
                    bank.questions.filter(
                      (q) => value === "all" || q.kind === value,
                    ).length
                  }
                </span>
              </button>
            ))}
          </div>
          <div>
            {visible.length ? (
              visible.map((q, i) => (
                <QuestionRow
                  key={q.id}
                  question={q}
                  index={i}
                  refresh={refresh}
                />
              ))
            ) : (
              <p className="learning-empty-note">
                No questions of this type yet. Generate more from your material.
              </p>
            )}
          </div>
        </>
      ) : (
        <div className="bank-empty">
          <span aria-hidden="true">?</span>
          <h3>Understanding starts with a good question.</h3>
          <p>
            We’ll create multiple-choice questions and definition pairs from
            this PDF. Only questions that pass source checks enter your games.
          </p>
          <p className="bank-limit">
            Up to 24 questions per generation · 5 generations per 24 hours
          </p>
        </div>
      )}
    </section>
  );
}
