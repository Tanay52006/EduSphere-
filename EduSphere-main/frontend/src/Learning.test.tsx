import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { api, type Me } from "./lib/api";
import { chain } from "./lib/chain";
import { activities } from "./lib/activities";
import { learning, type Bank, type LearningProgress } from "./lib/learning";
import { Games } from "./pages/Games";
import { QuestionBank } from "./pages/QuestionBank";
import { AuthScreen } from "./pages/AuthScreen";

const progress: LearningProgress = {
  total_xp: 75,
  today_xp: 75,
  level: 1,
  level_xp: 75,
  level_target: 150,
  tier: "Curious",
  streak: 1,
  longest_streak: 1,
  daily_goal: 20,
  daily_goal_met: true,
  activities: 1,
  badges: [],
};
const question: Bank["questions"][number] = {
  id: "q1",
  kind: "MCQ",
  prompt: "Which organelle releases usable energy?",
  options: ["Mitochondria", "Nucleus", "Membrane", "Ribosome"],
  answer: "Mitochondria",
  explanation: "Mitochondria release energy through respiration.",
  term: null,
  definition: null,
  validated: true,
  flagged: false,
  sources: [
    {
      chunk_id: "c1",
      page_start: 2,
      page_end: 2,
      url: "/api/documents/d1/file#page=2",
    },
  ],
};

function view(
  element: React.ReactNode,
  path = "/games",
  client = new QueryClient({ defaultOptions: { queries: { retry: false } } }),
) {
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>{element}</MemoryRouter>
    </QueryClientProvider>,
  );
  return client;
}
beforeEach(() => {
  vi.spyOn(activities, "catalog").mockResolvedValue({
    activities: [],
    preview_mode: false,
  });
  vi.spyOn(learning, "progress").mockResolvedValue(progress);
  vi.spyOn(chain, "journey").mockResolvedValue({
    chapter: "Energy of life",
    subject: "Biology",
    progress,
    levels: ["spark", "build", "oxygen", "repair", "mastery"].map((id, i) => ({
      id,
      title: id,
      icon: "chloroplast",
      mode: "connect",
      completed: false,
      unlocked: i === 0,
    })),
  });
});
afterEach(() => {
  vi.restoreAllMocks();
});

test("games empty state points to the library", async () => {
  vi.spyOn(api, "documents").mockResolvedValue([]);
  view(<Games />);
  expect(
    await screen.findByRole("link", { name: /Add your first material/ }),
  ).toHaveAttribute("href", "/library");
});

test("insufficient source-checked questions cannot start a game", async () => {
  vi.spyOn(api, "documents").mockResolvedValue([
    {
      id: "d1",
      original_filename: "Biology.pdf",
      status: "ready",
      page_count: 6,
      error_code: null,
      ocr_required: false,
      job_id: null,
      job_status: null,
      progress: 100,
      created_at: "2026-11-12",
    },
  ]);
  vi.spyOn(learning, "bank").mockResolvedValue({
    questions: [question],
    quality: null,
  });
  const start = vi.spyOn(learning, "start");
  view(<Games />);
  expect(
    await screen.findByRole("button", { name: /Play Quiz Blitz/ }),
  ).toBeDisabled();
  expect(
    screen.getByRole("button", { name: /Play Memory Match/ }),
  ).toBeDisabled();
  expect(screen.getByText(/1 ready/)).toBeInTheDocument();
  expect(start).not.toHaveBeenCalled();
});

test("question editing explains loss of validation and keeps the source link", async () => {
  const edit = vi
    .spyOn(learning, "edit")
    .mockResolvedValue({ ...question, validated: false });
  view(
    <QuestionBank
      documentId="d1"
      bank={{ questions: [question], quality: null }}
    />,
  );
  fireEvent.click(screen.getByRole("button", { name: "Edit prompt" }));
  expect(screen.getByText(/Edits remove validation/)).toBeInTheDocument();
  fireEvent.change(screen.getByRole("textbox", { name: "Question prompt" }), {
    target: { value: "An updated, clearer question?" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Save prompt" }));
  await waitFor(() =>
    expect(edit).toHaveBeenCalledWith("q1", "An updated, clearer question?"),
  );
  expect(
    screen.getByRole("link", { name: /Source · p. 2/, hidden: true }),
  ).toHaveAttribute("href", "/api/documents/d1/file#page=2");
});

test("removal requires explicit confirmation", () => {
  const remove = vi.spyOn(learning, "remove").mockResolvedValue(undefined);
  view(
    <QuestionBank
      documentId="d1"
      bank={{ questions: [question], quality: null }}
    />,
  );
  fireEvent.click(screen.getByRole("button", { name: "Remove" }));
  expect(remove).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Keep it" }));
  expect(
    screen.queryByRole("button", { name: "Remove question" }),
  ).not.toBeInTheDocument();
});

test("signing into another account clears cached private learning content", async () => {
  const me: Me = {
    user: { id: "u2", email: "second@example.com", created_at: "2026-11-12" },
    profile: {
      display_name: "Second learner",
      goal: null,
      timezone: "UTC",
      locale: "en",
      path_preference: "own_materials",
      notification_consent: { push: false, email: false, in_app: false },
      onboarding_completed: true,
    },
  };
  vi.spyOn(api, "login").mockResolvedValue(me);
  const client = new QueryClient();
  client.setQueryData(["questions", "private-document"], {
    questions: [question],
  });
  view(<AuthScreen mode="login" />, "/login", client);
  fireEvent.change(screen.getByLabelText("Email address"), {
    target: { value: "second@example.com" },
  });
  fireEvent.change(screen.getByLabelText("Password"), {
    target: { value: "long-test-password" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Log in" }));
  await waitFor(() => expect(client.getQueryData(["me"])).toEqual(me));
  expect(
    client.getQueryData(["questions", "private-document"]),
  ).toBeUndefined();
});

test("the authored game can be started without uploading personal material", async () => {
  vi.spyOn(api, "documents").mockResolvedValue([]);
  const start = vi
    .spyOn(chain, "start")
    .mockResolvedValue({ id: "chain-s1" } as never);
  view(<Games />);
  fireEvent.click(
    await screen.findByRole("button", { name: "Play Chain Reaction" }),
  );
  await waitFor(() =>
    expect(start).toHaveBeenCalledWith("spark", expect.anything()),
  );
  expect(screen.getByText("Biology · Starter chapter")).toBeInTheDocument();
});
