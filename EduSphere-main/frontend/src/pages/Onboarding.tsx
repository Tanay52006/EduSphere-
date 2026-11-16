import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import type { ApiError, Me, PathChoice } from "../lib/api";
import { api } from "../lib/api";
import {
  Button,
  Callout,
  Card,
  Input,
  ProgressBar,
  Switch,
  Textarea,
} from "../components/ui";

export function Onboarding({ me }: { me: Me }) {
  const [step, setStep] = useState(0);
  const [name, setName] = useState(me.profile.display_name ?? "");
  const [goal, setGoal] = useState(me.profile.goal ?? "");
  const [choice, setChoice] = useState<PathChoice | null>(null);
  const [notifications, setNotifications] = useState(false);
  const [error, setError] = useState("");
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const profileMutation = useMutation({
    mutationFn: () =>
      api.updateProfile({ display_name: name.trim(), goal: goal.trim() }),
    onSuccess: () => setStep(1),
    onError: (err: ApiError) => setError(err.message),
  });
  const completeMutation = useMutation({
    mutationFn: async () => {
      if (!choice) throw new Error("Choose a path to continue.");
      await api.updateProfile({
        notification_consent: {
          push: notifications,
          email: notifications,
          in_app: true,
        },
      });
      return api.completeOnboarding(choice);
    },
    onSuccess: (profile) => {
      queryClient.setQueryData<Me>(["me"], (old) =>
        old ? { ...old, profile } : old,
      );
      navigate("/");
    },
    onError: (err: Error) => setError(err.message),
  });
  const next = () => {
    setError("");
    if (step === 0) {
      if (!name.trim())
        return setError("Add your name so your home feels like yours.");
      profileMutation.mutate();
    } else if (step === 1) {
      if (!choice) return setError("Choose the way you want to begin.");
      setStep(2);
    } else completeMutation.mutate();
  };
  return (
    <main className="onboarding-page">
      <header className="onboarding-header">
        <Link to="/" className="brand">
          <span className="brand-mark">e</span> EduSphere
        </Link>
        <span>Step {step + 1} of 3</span>
      </header>
      <div className="onboarding-progress">
        <ProgressBar value={(step + 1) * 33.33} />
      </div>
      <section className="onboarding-content">
        {step === 0 && (
          <>
            <div className="eyebrow">A little context</div>
            <h1>Let’s make this yours{name ? `, ${name}` : ""}.</h1>
            <p className="lead">
              A good learning plan starts with knowing what matters to you.
            </p>
            <div className="onboarding-fields">
              <Input
                label="What should we call you?"
                name="display_name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Your name"
                autoFocus
              />
              <Textarea
                label="What are you working towards? (optional)"
                name="goal"
                value={goal}
                onChange={(event) => setGoal(event.target.value)}
                placeholder="For example: prepare for my biology exam in June"
                rows={4}
              />
            </div>
          </>
        )}
        {step === 1 && (
          <>
            <div className="eyebrow">Choose your starting point</div>
            <h1>What would you like to do?</h1>
            <p className="lead">
              You can always do both. For now, choose the door that feels most
              useful today.
            </p>
            <div className="choice-grid">
              <ChoiceCard
                selected={choice === "own_materials"}
                onClick={() => setChoice("own_materials")}
                icon="▥"
                title="Learn from my own materials"
                text="Turn your notes and PDFs into focused practice."
                tone="purple"
              />
              <ChoiceCard
                selected={choice === "learn_new"}
                onClick={() => setChoice("learn_new")}
                icon="✦"
                title="Learn something new"
                text="Build a guided path from a question or a spark."
                tone="blue"
              />
            </div>
          </>
        )}
        {step === 2 && (
          <>
            <div className="eyebrow">Stay in the loop</div>
            <h1>A gentle nudge, when you want it.</h1>
            <p className="lead">
              We’ll only use notifications to help with goals you set. You can
              change this later.
            </p>
            <Card className="notification-card">
              <div className="notification-icon">♧</div>
              <div>
                <h2>Helpful reminders</h2>
                <p>
                  Get a light reminder about your daily goal and reviews waiting
                  for you.
                </p>
              </div>
              <Switch
                label="Allow reminders"
                checked={notifications}
                onChange={setNotifications}
              />
            </Card>
            <Callout tone="yellow">
              Your learning space is private by default. We never send your
              notes anywhere without your say-so.
            </Callout>
          </>
        )}
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <div className="onboarding-actions">
          <Button
            variant="ghost"
            onClick={() => (step > 0 ? setStep(step - 1) : navigate("/login"))}
          >
            {step === 0 ? "Back to login" : "Back"}
          </Button>
          <Button
            onClick={next}
            loading={profileMutation.isPending || completeMutation.isPending}
          >
            {step === 2 ? "Take me home" : "Continue"}
          </Button>
        </div>
      </section>
    </main>
  );
}

function ChoiceCard({
  selected,
  onClick,
  icon,
  title,
  text,
  tone,
}: {
  selected: boolean;
  onClick: () => void;
  icon: string;
  title: string;
  text: string;
  tone: string;
}) {
  return (
    <button
      className={`choice-card choice-${tone} ${selected ? "is-selected" : ""}`}
      onClick={onClick}
      aria-pressed={selected}
    >
      <span className="choice-icon">{icon}</span>
      <span className="choice-copy">
        <strong>{title}</strong>
        <span>{text}</span>
      </span>
      <span className="choice-check">{selected ? "✓" : ""}</span>
    </button>
  );
}
