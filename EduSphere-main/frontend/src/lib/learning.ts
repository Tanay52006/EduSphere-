import { request } from "./api";

export interface Source {
  chunk_id: string;
  page_start: number;
  page_end: number;
  url: string;
}
export interface StudyQuestion {
  id: string;
  kind: "MCQ" | "MATCH";
  prompt: string;
  options: string[];
  answer: string;
  explanation: string;
  term: string | null;
  definition: string | null;
  sources: Source[];
  validated: boolean;
  flagged: boolean;
}
export interface Quality {
  generated: number;
  accepted: number;
  pass_rate: number;
}
export interface Bank {
  questions: StudyQuestion[];
  quality: Quality | null;
}
export type GameKind = "quiz_blitz" | "memory_match";
export interface LearningProgress {
  total_xp: number;
  today_xp: number;
  level: number;
  level_xp: number;
  level_target: number;
  tier: string;
  streak: number;
  longest_streak: number;
  daily_goal: number;
  daily_goal_met: boolean;
  activities: number;
  badges: { key: string; name: string; earned: boolean }[];
}
export interface Feedback {
  correct: boolean;
  timed_out?: boolean;
  answer?: string;
  explanation?: string;
  sources?: Source[];
}
export interface GameResult {
  id: string;
  game: GameKind;
  correct: number;
  total: number;
  accuracy: number;
  moves: number;
  duration_s: number;
  score: number;
  xp_earned: number;
  review: (Feedback & { question_id: string; prompt: string })[];
  progress: LearningProgress;
}
export interface PlaySession {
  id: string;
  game: GameKind;
  status: "open" | "finished" | "completed" | "abandoned";
  correct: number;
  total: number;
  index: number;
  lives: number;
  combo: number;
  score: number;
  moves: number;
  started_at: string;
  deadline?: number;
  paused: boolean;
  question?: { id: string; prompt: string; options: string[] };
  cards?: { id: string; text: string | null; matched: boolean }[];
  feedback: Feedback | null;
  result: GameResult | null;
}
const post = <T>(path: string, body: object = {}) =>
  request<T>(path, { method: "POST", body: JSON.stringify(body) });

export const learning = {
  bank: (documentId: string) =>
    request<Bank>(`/documents/${documentId}/questions`),
  generate: (documentId: string) =>
    post<Quality & { added: number }>(
      `/documents/${documentId}/questions/generate`,
    ),
  edit: (id: string, prompt: string) =>
    request<StudyQuestion>(`/questions/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ prompt }),
    }),
  flag: (id: string) => post<void>(`/questions/${id}/flag`),
  remove: (id: string) =>
    request<void>(`/questions/${id}`, { method: "DELETE" }),
  progress: () => request<LearningProgress>("/progress"),
  start: (document_id: string, game: GameKind) =>
    post<PlaySession>("/games/sessions", { document_id, game }),
  resume: (id: string) => request<PlaySession>(`/games/sessions/${id}`),
  answer: (id: string, question_id: string, choice: string) =>
    post<PlaySession>(`/games/sessions/${id}/answer`, { question_id, choice }),
  flip: (id: string, card_id: string) =>
    post<PlaySession>(`/games/sessions/${id}/flip`, { card_id }),
  submit: (id: string) => post<GameResult>(`/games/sessions/${id}/submit`),
  abandon: (id: string) => post<void>(`/games/sessions/${id}/abandon`),
  next: (id: string) => post<PlaySession>(`/games/sessions/${id}/next`),
  clock: (id: string, paused: boolean) =>
    post<PlaySession>(`/games/sessions/${id}/clock`, { paused }),
};
