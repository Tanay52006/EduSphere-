import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";
import {
  activities,
  type ActivityCard,
  type ActivitySession,
} from "./lib/activities";
import { ActivityPlay } from "./pages/ActivityPlay";
import { ActivityStudio } from "./components/ActivityStudio";

const game: ActivitySession = {
  id: "a1",
  status: "open",
  activity_id: "sample",
  attempts: 0,
  preview: false,
  activity: {
    title: "Rebuild the solution",
    subject: "Maths",
    mechanic: "sequence",
    goal: "Put these states in the right order.",
    why_fit: "The steps have a unique progression.",
    buckets: [],
    items: [
      { id: "n1", label: "Start" },
      { id: "n2", label: "Subtract" },
      { id: "n3", label: "Divide" },
      { id: "n4", label: "Check" },
    ],
  },
  draft: { order: ["n4", "n3", "n2", "n1"], assignments: {}, links: [] },
  feedback: null,
  result: null,
  sources: [{ title: "Source page", url: "/api/documents/d1/file#page=1" }],
};
function view(node = <ActivityPlay sessionId="a1" />) {
  return render(
    <QueryClientProvider
      client={
        new QueryClient({
          defaultOptions: {
            queries: { retry: false },
            mutations: { retry: false },
          },
        })
      }
    >
      <MemoryRouter>{node}</MemoryRouter>
    </QueryClientProvider>,
  );
}
afterEach(() => vi.restoreAllMocks());

test("reordering and undo preserve cards; only server feedback determines the result", async () => {
  vi.spyOn(activities, "resume").mockResolvedValue(game);
  const run = vi.spyOn(activities, "run").mockResolvedValue({
    ...game,
    attempts: 1,
    feedback: {
      correct: false,
      message: "Start comes first.",
      misplaced: ["n4", "n1"],
      broken: null,
      powered: [],
    },
  });
  view();
  fireEvent.click(await screen.findByRole("button", { name: "Move Start up" }));
  expect(screen.getByRole("button", { name: "Start" })).toHaveFocus();
  fireEvent.click(screen.getByRole("button", { name: "Undo last move" }));
  fireEvent.click(screen.getByRole("button", { name: "Check solution" }));
  await waitFor(() => expect(run).toHaveBeenCalledWith("a1", game.draft));
  expect(await screen.findByText("Start comes first.")).toBeInTheDocument();
  expect(screen.queryByText(/XP/)).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Move Start up" }));
  expect(screen.queryByText("Start comes first.")).not.toBeInTheDocument();
});

test("sorting requires every card and allows changing a placement before checking", async () => {
  const sorted: ActivitySession = {
    ...game,
    activity: {
      ...game.activity,
      mechanic: "sort",
      buckets: [
        { id: "b1", label: "Left", rule: "The first category rule." },
        { id: "b2", label: "Right", rule: "The second category rule." },
      ],
    },
    draft: { order: [], assignments: {}, links: [] },
  };
  vi.spyOn(activities, "resume").mockResolvedValue(sorted);
  const run = vi.spyOn(activities, "run").mockResolvedValue(sorted);
  view();
  const check = await screen.findByRole("button", { name: "Check solution" });
  expect(check).toBeDisabled();
  for (const label of ["Start", "Subtract", "Divide", "Check"]) {
    fireEvent.click(screen.getByRole("button", { name: label }));
    fireEvent.click(
      screen.getByRole("button", { name: "Place selected sample in Left" }),
    );
  }
  fireEvent.click(screen.getByRole("button", { name: "Check" }));
  fireEvent.click(
    screen.getByRole("button", { name: "Place selected sample in Right" }),
  );
  fireEvent.click(check);
  await waitFor(() =>
    expect(run).toHaveBeenCalledWith("a1", {
      order: [],
      assignments: { n1: "b1", n2: "b1", n3: "b1", n4: "b2" },
      links: [],
    }),
  );
});

test("a system uses the existing accessible connection board", async () => {
  const connected = {
    ...game,
    activity: { ...game.activity, mechanic: "connections" as const },
    draft: { order: [], assignments: {}, links: [] },
  };
  vi.spyOn(activities, "resume").mockResolvedValue(connected);
  const run = vi.spyOn(activities, "run").mockResolvedValue(connected);
  view();
  fireEvent.click(
    await screen.findByRole("button", { name: "Connect from Start" }),
  );
  fireEvent.click(screen.getByRole("button", { name: "Connect to Subtract" }));
  fireEvent.click(screen.getByRole("button", { name: "Run system" }));
  await waitFor(() =>
    expect(run).toHaveBeenCalledWith("a1", {
      order: [],
      assignments: {},
      links: [["n1", "n2"]],
    }),
  );
});

test("material generation sends the focus and exposes the returned playable game", async () => {
  const card: ActivityCard = {
    id: "generated-1",
    title: "Find the family",
    subject: "Chemistry",
    mechanic: "sort",
    goal: "Classify the samples.",
    why_fit: "The source states categories.",
    size: 4,
    generated: true,
    document_id: "d1",
    preview: true,
  };
  const catalog = vi
    .spyOn(activities, "catalog")
    .mockResolvedValue({ activities: [], preview_mode: true });
  const generate = vi
    .spyOn(activities, "generate")
    .mockImplementation(async () => {
      catalog.mockResolvedValue({ activities: [card], preview_mode: true });
      return card;
    });
  const start = vi.spyOn(activities, "start").mockResolvedValue(game);
  view(<ActivityStudio documentId="d1" />);
  fireEvent.change(screen.getByRole("textbox"), {
    target: { value: "Classification of matter" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Create a game" }));
  await waitFor(() =>
    expect(generate).toHaveBeenCalledWith("d1", "Classification of matter"),
  );
  fireEvent.click(
    await screen.findByRole("button", { name: "Play Find the family" }),
  );
  await waitFor(() =>
    expect(start).toHaveBeenCalledWith("generated-1", expect.anything()),
  );
  expect(screen.getByText(/Development preview ready/)).toBeInTheDocument();
});
