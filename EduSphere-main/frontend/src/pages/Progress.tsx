import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Skeleton } from "../components/ui";
import { LearningError } from "../components/LearningUI";
import { ArenaIcon, type ArenaIconName } from "../components/ArenaIcon";
import { learning } from "../lib/learning";

const milestones: { icon: ArenaIconName; requirement: string }[] = [
  { icon: "play", requirement: "Finish 1 game" },
  { icon: "target", requirement: "Score 10/10" },
  { icon: "flame", requirement: "3-day streak" },
  { icon: "shield", requirement: "7-day streak" },
];

export function Progress() {
  const query = useQuery({
    queryKey: ["progress"],
    queryFn: learning.progress,
    retry: false,
  });
  if (query.isPending) return <Skeleton className="play-loading" />;
  if (query.isError)
    return (
      <div className="learning-content">
        <LearningError error={query.error} retry={() => void query.refetch()} />
      </div>
    );
  const p = query.data;
  const levelRatio = p.level_xp / p.level_target;
  const goalRatio = Math.min(1, p.today_xp / p.daily_goal);
  return (
    <div className="learning-content progress-page">
      <section className="learning-heading arena-heading">
        <div>
          <p className="eyebrow">Your record</p>
          <h2>Progress</h2>
        </div>
        <Link className="button button-primary" to="/games">
          <ArenaIcon name="play" size={17} />
          Play a game
        </Link>
      </section>
      <section className="player-overview" aria-label="Learning progress">
        <div className="player-level">
          <div
            className="level-ring"
            role="progressbar"
            aria-label="Level progress"
            aria-valuemin={0}
            aria-valuemax={p.level_target}
            aria-valuenow={p.level_xp}
          >
            <svg viewBox="0 0 120 120" aria-hidden="true">
              <circle className="ring-track" cx="60" cy="60" r="53" />
              <circle
                className="ring-value"
                cx="60"
                cy="60"
                r="53"
                pathLength="100"
                strokeDasharray={`${levelRatio * 100} 100`}
              />
            </svg>
            <span>
              <small>LEVEL</small>
              <strong>{p.level}</strong>
            </span>
          </div>
          <div className="level-details">
            <span className="eyebrow">{p.tier}</span>
            <h3>
              {p.total_xp.toLocaleString()} <small>XP</small>
            </h3>
            <p>
              {p.level_target - p.level_xp} XP to level {p.level + 1}
            </p>
            <div className="level-segments" aria-hidden="true">
              {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((i) => (
                <i key={i} className={levelRatio * 10 > i ? "filled" : ""} />
              ))}
            </div>
          </div>
        </div>
        <div className="record-stat streak-stat">
          <ArenaIcon name="flame" size={29} />
          <span>Current streak</span>
          <strong>
            {p.streak}
            <small>day{p.streak !== 1 ? "s" : ""}</small>
          </strong>
          <p>Best: {p.longest_streak} days</p>
        </div>
        <div className="record-stat daily-stat">
          <ArenaIcon name={p.daily_goal_met ? "check" : "target"} size={29} />
          <span>Daily goal</span>
          <strong>
            {Math.min(100, Math.round(goalRatio * 100))}
            <small>%</small>
          </strong>
          <div
            className="round-track"
            role="progressbar"
            aria-label="Daily XP goal"
            aria-valuemin={0}
            aria-valuemax={p.daily_goal}
            aria-valuenow={Math.min(p.today_xp, p.daily_goal)}
          >
            <span style={{ transform: `scaleX(${goalRatio})` }} />
          </div>
          <p>
            {p.today_xp} / {p.daily_goal} XP
          </p>
        </div>
      </section>
      <section className="badge-section">
        <div className="section-heading">
          <h3>Achievements</h3>
          <span>
            {p.badges.filter((b) => b.earned).length} / {p.badges.length}{" "}
            unlocked
          </span>
        </div>
        <div className="badge-grid">
          {p.badges.map((badge, i) => (
            <div
              key={badge.key}
              className={`badge-item ${badge.earned ? "badge-earned" : ""}`}
            >
              <span className="badge-symbol">
                <ArenaIcon name={milestones[i]?.icon ?? "trophy"} size={28} />
              </span>
              <div>
                <strong>{badge.name}</strong>
                <small>{milestones[i]?.requirement}</small>
              </div>
              <span
                className="badge-status"
                aria-label={badge.earned ? "Earned" : "Locked"}
              >
                <ArenaIcon name={badge.earned ? "check" : "lock"} size={15} />
              </span>
            </div>
          ))}
        </div>
      </section>
      <div className="record-summary">
        <ArenaIcon name="games" size={20} />
        <span>
          <strong>{p.activities}</strong> games completed
        </span>
        <span>
          <ArenaIcon name="shield" size={17} />
          Weekly streak freeze included
        </span>
      </div>
    </div>
  );
}
