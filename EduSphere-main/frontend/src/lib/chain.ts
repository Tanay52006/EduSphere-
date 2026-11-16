import { request } from "./api";
import type { LearningProgress } from "./learning";

export type LinkPair = [string, string];
export interface ChainNode {
  id: string;
  label: string;
  kind: string;
  x: number;
  y: number;
  mx: number;
  my: number;
  input: boolean;
  output: boolean;
}
export interface ChainLevel {
  id: string;
  title: string;
  icon: string;
  mode: string;
  completed: boolean;
  unlocked: boolean;
}
export interface ChainJourney {
  chapter: string;
  subject: string;
  levels: ChainLevel[];
  progress: LearningProgress;
}
export interface ChainSession {
  id: string;
  status: string;
  level_id: string;
  title: string;
  goal: string;
  mode: string;
  hint: string;
  nodes: ChainNode[];
  links: LinkPair[];
  process: string | null;
  prediction?: string | null;
  prediction_prompt?: string | null;
  prediction_options?: string[];
  attempts: number;
  choices: { id: string; label: string; kind: string }[];
  source: { title: string; url: string };
  feedback: {
    correct: boolean;
    message: string;
    broken: LinkPair | null;
    powered: LinkPair[];
    stalled?: string | null;
  } | null;
  result: { xp_earned: number; progress: LearningProgress } | null;
}
export const chain = {
  journey: () => request<ChainJourney>("/chain"),
  start: (level_id: string) =>
    request<ChainSession>("/chain/start", {
      method: "POST",
      body: JSON.stringify({ level_id }),
    }),
  resume: (id: string) => request<ChainSession>(`/chain/sessions/${id}`),
  run: (
    id: string,
    links: LinkPair[],
    process: string | null,
    prediction: string | null = null,
  ) =>
    request<ChainSession>(`/chain/sessions/${id}/run`, {
      method: "POST",
      body: JSON.stringify({ links, process, prediction }),
    }),
};
