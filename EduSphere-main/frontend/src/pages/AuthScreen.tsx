import type { FormEvent } from "react";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { ApiError, api } from "../lib/api";
import { Button, Callout, Input } from "../components/ui";

export function AuthScreen({ mode }: { mode: "login" | "signup" }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const mutation = useMutation({
    mutationFn: () =>
      mode === "login"
        ? api.login(email, password)
        : api.signup(email, password),
    onSuccess: (data) => {
      queryClient.clear();
      queryClient.setQueryData(["me"], data);
      navigate(data.profile.onboarding_completed ? "/" : "/onboarding");
    },
    onError: (err: ApiError) => setError(err.message),
  });
  const submit = (event: FormEvent) => {
    event.preventDefault();
    setError("");
    if (!email.includes("@")) return setError("Enter a valid email address.");
    if (password.length < 10)
      return setError("Use at least 10 characters for your password.");
    mutation.mutate();
  };
  return (
    <main className="auth-page">
      <div className="auth-aside">
        <Link to="/login" className="brand">
          <span className="brand-mark">e</span> EduSphere
        </Link>
        <div className="aside-quote">
          <p>Make your notes playable.</p>
          <span>Learning that meets you where you are.</span>
        </div>
        <div className="aside-orbit orbit-one" />
        <div className="aside-orbit orbit-two" />
      </div>
      <section className="auth-panel">
        <div className="auth-form-wrap">
          <span className="mobile-brand brand">
            <span className="brand-mark">e</span> EduSphere
          </span>
          <div className="eyebrow">Your learning home</div>
          <h1>
            {mode === "login"
              ? "Welcome back."
              : "Start learning with intention."}
          </h1>
          <p className="lead">
            {mode === "login"
              ? "Pick up where you left off."
              : "Turn your materials or a new curiosity into momentum."}
          </p>
          {error && <Callout tone="red">{error}</Callout>}
          <form onSubmit={submit}>
            <Input
              label="Email address"
              name="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
            />
            <Input
              label="Password"
              name="password"
              type="password"
              autoComplete={
                mode === "login" ? "current-password" : "new-password"
              }
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="10 characters minimum"
            />
            <Button
              type="submit"
              className="full-button"
              loading={mutation.isPending}
            >
              {mode === "login" ? "Log in" : "Create account"}
            </Button>
          </form>
          <p className="auth-switch">
            {mode === "login"
              ? "New to EduSphere?"
              : "Already have an account?"}{" "}
            <Link to={mode === "login" ? "/signup" : "/login"}>
              {mode === "login" ? "Create an account" : "Log in"}
            </Link>
          </p>
        </div>
      </section>
    </main>
  );
}
