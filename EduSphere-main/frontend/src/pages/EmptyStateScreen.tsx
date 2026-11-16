import { useMemo } from "react";
import { Button, EmptyState } from "../components/ui";

export function EmptyStateScreen({
  title,
  icon,
}: {
  title: string;
  icon: string;
}) {
  const copy = useMemo(
    () =>
      ({
        Library: [
          "Your library is quiet for now.",
          "Add a note or PDF and we’ll turn it into focused practice.",
        ],
        Paths: [
          "No paths yet.",
          "Choose a topic and we’ll help you find a clear way in.",
        ],
        Games: [
          "Your games will live here.",
          "Study from your materials to create your first playable set.",
        ],
        Progress: [
          "Your progress will take shape here.",
          "Complete a session and come back to see your learning rhythm.",
        ],
      })[title] ?? ["Nothing here yet.", "This space is ready when you are."],
    [title],
  );
  return (
    <div className="empty-page">
      <EmptyState icon={icon} title={copy[0]}>
        {copy[1]}
      </EmptyState>
      <Button variant="secondary">Go to Home</Button>
    </div>
  );
}
