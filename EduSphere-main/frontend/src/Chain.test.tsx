import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";
import { chain, type ChainSession } from "./lib/chain";
import { ChainPlay } from "./pages/ChainPlay";

const game: ChainSession = {
  id: "s1",
  status: "open",
  level_id: "build",
  title: "Make the connection",
  goal: "Build the energy pathway",
  mode: "connect",
  hint: "Tap an output, then an input.",
  nodes: [
    {
      id: "photo",
      label: "Photosynthesis",
      kind: "chloroplast",
      x: 200,
      y: 200,
      mx: 80,
      my: 80,
      input: false,
      output: true,
    },
    {
      id: "atp",
      label: "ATP",
      kind: "battery",
      x: 600,
      y: 200,
      mx: 200,
      my: 280,
      input: true,
      output: false,
    },
  ],
  links: [],
  process: null,
  attempts: 0,
  choices: [],
  source: {
    title: "Biology",
    url: "https://openstax.org/books/biology-2e/pages/7-introduction",
  },
  feedback: null,
  result: null,
};
function view() {
  render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <MemoryRouter>
        <ChainPlay sessionId="s1" />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}
afterEach(() => vi.restoreAllMocks());

test("connections are reversible and only the server can confirm a solved board", async () => {
  vi.spyOn(chain, "resume").mockResolvedValue(game);
  const run = vi.spyOn(chain, "run").mockResolvedValue({
    ...game,
    links: [["photo", "atp"]],
    feedback: {
      correct: false,
      message: "This route skips a process.",
      broken: ["photo", "atp"],
      powered: [],
    },
  });
  view();
  await screen.findByRole("heading", { name: "Build the energy pathway" });
  fireEvent.click(
    screen.getByRole("button", { name: "Connect from Photosynthesis" }),
  );
  fireEvent.click(screen.getByRole("button", { name: "Connect to ATP" }));
  expect(
    screen.getByRole("button", { name: "Remove Photosynthesis to ATP" }),
  ).toBeInTheDocument();
  expect(run).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Undo last move" }));
  expect(
    screen.queryByRole("button", { name: "Remove Photosynthesis to ATP" }),
  ).not.toBeInTheDocument();
  fireEvent.click(
    screen.getByRole("button", { name: "Connect from Photosynthesis" }),
  );
  fireEvent.click(screen.getByRole("button", { name: "Connect to ATP" }));
  fireEvent.click(screen.getByRole("button", { name: "RUN" }));
  await waitFor(() =>
    expect(run).toHaveBeenCalledWith("s1", [["photo", "atp"]], null, null),
  );
  expect(
    await screen.findByText("This route skips a process."),
  ).toBeInTheDocument();
  expect(screen.queryByText(/XP/)).not.toBeInTheDocument();
});

test("a completed board stays locked after reload and displays the saved reward", async () => {
  vi.spyOn(chain, "resume").mockResolvedValue({
    ...game,
    status: "completed",
    feedback: {
      correct: true,
      message: "It works.",
      broken: null,
      powered: [["photo", "atp"]],
    },
    result: { xp_earned: 25, progress: {} as never },
  });
  view();
  expect(await screen.findByText("+25 XP")).toBeInTheDocument();
  expect(document.querySelector(".chain-play")).toHaveAttribute(
    "data-motion",
    "complete",
  );
  expect(document.querySelector(".run-success")).not.toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: "Connect from Photosynthesis" }),
  ).toBeDisabled();
  expect(screen.queryByRole("button", { name: "RUN" })).not.toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: "Next challenge" }),
  ).toBeInTheDocument();
});

test("a placed process can be cleared or dropped into its station without running it", async () => {
  vi.spyOn(chain, "resume").mockResolvedValue({
    ...game,
    mode: "place",
    nodes: [
      {
        ...game.nodes[0],
        id: "process",
        label: "Missing process",
        kind: "slot",
      },
    ],
    choices: [
      { id: "respiration", label: "Respiration", kind: "mitochondria" },
    ],
  });
  const run = vi.spyOn(chain, "run");
  view();
  const choice = await screen.findByRole("button", { name: "Respiration" });
  expect(screen.getByRole("button", { name: "RUN" })).toBeDisabled();
  fireEvent.click(choice);
  expect(choice).toHaveAttribute("aria-pressed", "true");
  fireEvent.click(choice);
  expect(screen.getByRole("button", { name: "RUN" })).toBeDisabled();
  fireEvent.drop(document.querySelector(".node-process")!, {
    dataTransfer: { getData: () => "respiration" },
  });
  expect(screen.getByRole("button", { name: "RUN" })).toBeEnabled();
  expect(run).not.toHaveBeenCalled();
});

test("the oxygen challenge requires a forecast and submits it to the server", async () => {
  vi.spyOn(chain, "resume").mockResolvedValue({
    ...game,
    prediction_prompt: "Which process still makes ATP?",
    prediction_options: ["glycolysis", "fermentation"],
    nodes: [
      { ...game.nodes[0], id: "glycolysis", label: "Glycolysis" },
      { ...game.nodes[1], id: "fermentation", label: "Fermentation" },
    ],
  });
  const run = vi.spyOn(chain, "run").mockResolvedValue({
    ...game,
    feedback: {
      correct: false,
      message: "Reconsider the energy producer.",
      broken: null,
      powered: [],
    },
  });
  view();
  const runButton = await screen.findByRole("button", { name: "RUN" });
  expect(runButton).toBeDisabled();
  fireEvent.click(
    screen.getByRole("button", { name: "Predict: Fermentation produces ATP" }),
  );
  expect(runButton).toBeEnabled();
  fireEvent.click(runButton);
  await waitFor(() =>
    expect(run).toHaveBeenCalledWith("s1", [], null, "fermentation"),
  );
  expect(
    await screen.findByText("Reconsider the energy producer."),
  ).toBeInTheDocument();
  expect(screen.queryByText(/XP/)).not.toBeInTheDocument();
});
