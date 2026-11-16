import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Button, Card, EmptyState, Tag } from "../components/ui";
import { learning } from "../lib/learning";

function formatHomeDate(timezone: string, date = new Date()) {
  const options: Intl.DateTimeFormatOptions = {
    weekday: "long",
    day: "numeric",
    month: "long",
    timeZone: timezone,
  };
  try {
    return new Intl.DateTimeFormat(undefined, options).format(date);
  } catch {
    return new Intl.DateTimeFormat(undefined, {
      ...options,
      timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    }).format(date);
  }
}

function getGreeting(timezone: string, date = new Date()) {
  let hour: number;
  try {
    hour = Number(
      new Intl.DateTimeFormat("en-US", {
        hour: "numeric",
        hourCycle: "h23",
        timeZone: timezone,
      }).format(date),
    );
  } catch {
    hour = date.getHours();
  }
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

export function Home({
  firstName,
  timezone,
  onToast,
}: {
  firstName: string;
  timezone: string;
  onToast: (message: string) => void;
}) {
  const today = useMemo(() => formatHomeDate(timezone), [timezone]);
  const greeting = useMemo(() => getGreeting(timezone), [timezone]);
  const navigate = useNavigate();
  const progress = useQuery({
    queryKey: ["progress"],
    queryFn: learning.progress,
    retry: false,
  });
  const p = progress.data;
  return (
    <div className="home-content">
      <section className="welcome-block">
        <div>
          <p className="eyebrow">{today}</p>
          <h2>
            {greeting}, {firstName}.
          </h2>
          <p className="lead">A small step today keeps the thread going.</p>
        </div>
        <div className="streak-chip">
          <span>♨</span>
          <strong>{p?.streak ?? 0}</strong>
          <small>
            {p?.streak
              ? "Days of making connections"
              : "Start your streak today"}
          </small>
        </div>
      </section>
      <section className="home-grid">
        <Card className="daily-card">
          <div className="card-topline">
            <Tag tone="yellow">Today’s focus</Tag>
          </div>
          <h2>Begin a learning session</h2>
          <p>
            Turn your notes into questions, make a few connections, and give
            your curiosity a little room.
          </p>
          <div className="session-row">
            <div className="session-icon purple">▥</div>
            <div>
              <strong>Study from your materials</strong>
              <span>Review a note or play a quick game</span>
            </div>
            <Button variant="secondary" onClick={() => navigate("/games")}>
              Start
            </Button>
          </div>
          <div className="session-row">
            <div className="session-icon blue">✦</div>
            <div>
              <strong>Explore something new</strong>
              <span>Build a guided path from a topic</span>
            </div>
            <Button
              variant="secondary"
              onClick={() =>
                onToast(
                  "Guided paths are coming soon. Start with your materials for now.",
                )
              }
            >
              Start
            </Button>
          </div>
        </Card>
        <Card className="progress-card">
          <div className="card-topline">
            <Tag tone="green">Your progress</Tag>
          </div>
          {p && p.activities > 0 ? (
            <div className="home-live-progress">
              <strong>
                {p.total_xp.toLocaleString()} <small>XP</small>
              </strong>
              <p>
                Level {p.level} · {p.tier}
              </p>
              <span>
                {p.today_xp} XP today{" "}
                {p.daily_goal_met
                  ? "· Daily goal reached ✓"
                  : `· ${p.daily_goal} XP gentle goal`}
              </span>
            </div>
          ) : (
            <EmptyState icon="↗" title="No progress to show yet.">
              Complete a learning session and your progress will appear here.
            </EmptyState>
          )}
          <button className="text-button" onClick={() => navigate("/progress")}>
            See your progress <span>→</span>
          </button>
        </Card>
      </section>
      <section className="home-lower">
        <div className="section-heading">
          <div>
            <p className="eyebrow">A place to return to</p>
            <h2>Pick up where you left off</h2>
          </div>
          <button className="text-button" onClick={() => navigate("/library")}>
            View library →
          </button>
        </div>
        <div className="empty-strip">
          <span className="empty-strip-icon">＋</span>
          <div>
            <strong>There’s a little more to discover in your notes.</strong>
            <p>Add a PDF, build your question bank, and make it playable.</p>
          </div>
          <Button variant="ghost" onClick={() => navigate("/library")}>
            Add something
          </Button>
        </div>
      </section>
    </div>
  );
}
