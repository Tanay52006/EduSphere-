import { request } from "./api";
import type { LearningProgress } from "./learning";

export type Mechanic = "sequence" | "sort" | "connections";
export const mechanicNames: Record<Mechanic, string> = {
  sequence: "Rebuild",
  sort: "Rule sort",
  connections: "System builder",
};
export interface ActivityCard {
  id: string;
  title: string;
  subject: string;
  mechanic: Mechanic;
  goal: string;
  why_fit: string;
  size: number;
  generated: boolean;
  document_id: string | null;
  preview: boolean;
}
export interface ActivityDraft {
  order: string[];
  assignments: Record<string, string>;
  links: [string, string][];
}
export interface ActivitySession {
  id: string;
  status: "open" | "completed" | "abandoned";
  activity_id: string;
  activity: {
    title: string;
    subject: string;
    mechanic: Mechanic;
    goal: string;
    why_fit: string;
    items: { id: string; label: string }[];
    buckets: { id: string; label: string; rule: string }[];
  };
  draft: ActivityDraft;
  attempts: number;
  preview: boolean;
  feedback: {
    correct: boolean;
    message: string;
    misplaced: string[];
    broken: [string, string] | null;
    powered: [string, string][];
  } | null;
  result: {
    xp_earned: number;
    explanation: string;
    progress: LearningProgress;
  } | null;
  sources: { title: string; url: string }[];
}
export const activities = {
  catalog: () =>
    request<{ activities: ActivityCard[]; preview_mode: boolean }>(
      "/activities",
    ),
  generate: (document_id: string, focus: string) =>
    request<ActivityCard>("/activities/generate", {
      method: "POST",
      body: JSON.stringify({ document_id, focus }),
    }),
  start: (activity_id: string) =>
    request<ActivitySession>("/activities/start", {
      method: "POST",
      body: JSON.stringify({ activity_id }),
    }),
  resume: (id: string) =>
    request<ActivitySession>(`/activities/sessions/${id}`),
  run: (id: string, draft: ActivityDraft) =>
    request<ActivitySession>(`/activities/sessions/${id}/run`, {
      method: "POST",
      body: JSON.stringify(draft),
    }),
};
