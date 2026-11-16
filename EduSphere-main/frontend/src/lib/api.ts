export type PathChoice = "own_materials" | "learn_new";
export interface User {
  id: string;
  email: string;
  created_at: string;
}
export interface Profile {
  display_name: string | null;
  goal: string | null;
  timezone: string;
  locale: string;
  path_preference: PathChoice | null;
  notification_consent: { push: boolean; email: boolean; in_app: boolean };
  onboarding_completed: boolean;
}
export interface Me {
  user: User;
  profile: Profile;
}
export interface SearchHit {
  chunk_id: string;
  document_id: string;
  text: string;
  page_start: number;
  page_end: number;
  heading: string | null;
  score: number;
  sources: string[];
}
export interface SearchResponse {
  query: string;
  results: SearchHit[];
}
export interface ChatCitation {
  chunk_id: string;
  document_id: string;
  page_start: number;
  page_end: number;
}
export interface ChatResponse {
  answer: string;
  citations: ChatCitation[];
  grounded: boolean;
}
export interface DocumentItem {
  id: string;
  original_filename: string;
  status: string;
  error_code: string | null;
  page_count: number;
  ocr_required: boolean;
  job_id: string | null;
  job_status: string | null;
  progress: number;
  created_at: string;
}
export interface ApiErrorShape {
  error: { code: string; message: string };
  request_id: string;
}
export class ApiError extends Error {
  code: string;
  status: number;
  constructor(message: string, code: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }
}
const isMock =
  import.meta.env.VITE_API_MOCK === "1" || import.meta.env.MODE === "test";
let mockMe: Me | null = null;
const defaultProfile = (): Profile => ({
  display_name: null,
  goal: null,
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
  locale: "en",
  path_preference: null,
  notification_consent: { push: false, email: false, in_app: false },
  onboarding_completed: false,
});
function mockError(message: string, code: string, status: number): never {
  throw new ApiError(message, code, status);
}
async function mockRequest<T>(
  path: string,
  body?: Record<string, unknown>,
): Promise<T> {
  await new Promise((resolve) => setTimeout(resolve, 80));
  if (path === "/auth/me") {
    if (!mockMe)
      mockError("You need to log in to continue.", "unauthenticated", 401);
    return mockMe as T;
  }
  if (path === "/auth/logout") {
    mockMe = null;
    return undefined as T;
  }
  if (path === "/auth/login" || path === "/auth/signup") {
    const email = String(body?.email ?? "")
      .trim()
      .toLowerCase();
    const password = String(body?.password ?? "");
    if (!email.includes("@") || password.length < 10)
      mockError(
        "Enter a valid email and a password of at least 10 characters.",
        "validation_error",
        422,
      );
    if (path === "/auth/login" && email.includes("wrong"))
      mockError("Email or password is incorrect.", "invalid_credentials", 401);
    if (path === "/auth/signup" && email.includes("taken"))
      mockError(
        "That email is already in use. Try logging in instead.",
        "account_unavailable",
        409,
      );
    mockMe = {
      user: {
        id: crypto.randomUUID(),
        email,
        created_at: new Date().toISOString(),
      },
      profile: defaultProfile(),
    };
    return mockMe as T;
  }
  if (!mockMe)
    mockError("You need to log in to continue.", "unauthenticated", 401);
  if (path === "/profile") {
    mockMe = { ...mockMe, profile: { ...mockMe.profile, ...body } as Profile };
    return mockMe.profile as T;
  }
  if (path === "/onboarding/complete") {
    mockMe = {
      ...mockMe,
      profile: {
        ...mockMe.profile,
        path_preference: body?.path_choice as PathChoice,
        onboarding_completed: true,
      },
    };
    return mockMe.profile as T;
  }
  if (path === "/search") {
    return { query: String(body?.q ?? ""), results: [] } as T;
  }
  if (path === "/documents") return [] as T;
  if (path === "/progress")
    return {
      total_xp: 0,
      today_xp: 0,
      level: 1,
      level_xp: 0,
      level_target: 150,
      tier: "Curious",
      streak: 0,
      longest_streak: 0,
      daily_goal: 20,
      daily_goal_met: false,
      activities: 0,
      badges: [],
    } as T;
  mockError("The requested action is not available.", "not_found", 404);
}
function csrfToken() {
  return document.cookie
    .split("; ")
    .find((cookie) => cookie.startsWith("edu_csrf="))
    ?.split("=")[1];
}
export async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  if (isMock)
    return mockRequest<T>(
      path,
      options.body ? JSON.parse(String(options.body)) : undefined,
    );
  const method = options.method ?? "GET";
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData))
    headers.set("Content-Type", "application/json");
  if (!["GET", "HEAD"].includes(method) && csrfToken())
    headers.set("X-CSRF-Token", csrfToken()!);
  const response = await fetch(`/api${path}`, {
    ...options,
    headers,
    credentials: "include",
  });
  if (response.status === 204) return undefined as T;
  const data = (await response.json()) as T | ApiErrorShape;
  if (!response.ok) {
    const error = data as ApiErrorShape;
    throw new ApiError(
      error.error?.message ?? "Something went wrong.",
      error.error?.code ?? "unknown",
      response.status,
    );
  }
  return data as T;
}
export const api = {
  me: () => request<Me>("/auth/me"),
  login: (email: string, password: string) =>
    request<Me>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  signup: (email: string, password: string) =>
    request<Me>("/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  logout: () => request<void>("/auth/logout", { method: "POST" }),
  updateProfile: (body: Partial<Profile>) =>
    request<Profile>("/profile", {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  completeOnboarding: (path_choice: PathChoice) =>
    request<Profile>("/onboarding/complete", {
      method: "POST",
      body: JSON.stringify({ path_choice }),
    }),
  search: (query: string, top_k = 5) =>
    isMock
      ? mockRequest<SearchResponse>("/search", { q: query, top_k })
      : request<SearchResponse>(
          `/search?q=${encodeURIComponent(query)}&top_k=${top_k}`,
        ),
  documents: () => request<DocumentItem[]>("/documents"),
  uploadDocument: (file: File) => {
    if (isMock)
      return Promise.reject(
        new ApiError(
          "Uploads require the running backend.",
          "not_available",
          503,
        ),
      );
    const body = new FormData();
    body.append("file", file);
    return request<DocumentItem>("/documents", { method: "POST", body });
  },
  chat: (question: string, top_k = 5) => {
    if (isMock)
      return Promise.reject(
        new ApiError(
          "Chat requires the running backend.",
          "not_available",
          503,
        ),
      );
    return request<ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify({ question, top_k }),
    });
  },
};
export const resetMock = () => {
  mockMe = null;
};
