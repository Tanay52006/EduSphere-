import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, test } from "vitest";
import App from "./App";
import { resetMock } from "./lib/api";

function renderApp(path: string) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  resetMock();
});
afterEach(() => {
  localStorage.clear();
});

test("guards an unauthenticated user to login", async () => {
  renderApp("/");
  expect(
    await screen.findByRole("heading", { name: "Welcome back." }),
  ).toBeInTheDocument();
});

test("validates the login form without an API request", async () => {
  renderApp("/login");
  fireEvent.click(await screen.findByRole("button", { name: "Log in" }));
  expect(screen.getByText("Enter a valid email address.")).toBeInTheDocument();
});

test("uses the primary button style for login submission", async () => {
  renderApp("/login");
  expect(await screen.findByRole("button", { name: "Log in" })).toHaveClass(
    "button",
    "button-primary",
  );
});

test("supports a keyboard-only path through login", async () => {
  renderApp("/login");
  const email = await screen.findByLabelText("Email address");
  email.focus();
  fireEvent.change(email, { target: { value: "student@example.com" } });
  const password = screen.getByLabelText("Password");
  password.focus();
  expect(password).toHaveFocus();
  fireEvent.change(password, { target: { value: "long-enough-password" } });
  screen.getByRole("button", { name: "Log in" }).focus();
  expect(screen.getByRole("button", { name: "Log in" })).toHaveFocus();
});

test("shows mock API errors for invalid credentials", async () => {
  renderApp("/login");
  fireEvent.change(await screen.findByLabelText("Email address"), {
    target: { value: "wrong@example.com" },
  });
  fireEvent.change(screen.getByLabelText("Password"), {
    target: { value: "long-enough-password" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Log in" }));
  expect(
    await screen.findByText("Email or password is incorrect."),
  ).toBeInTheDocument();
});

test("moves through onboarding and submits the selected fork", async () => {
  renderApp("/signup");
  fireEvent.change(await screen.findByLabelText("Email address"), {
    target: { value: "student@example.com" },
  });
  fireEvent.change(screen.getByLabelText("Password"), {
    target: { value: "long-enough-password" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Create account" }));
  expect(
    await screen.findByRole("heading", { name: /Let’s make this yours/ }),
  ).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("What should we call you?"), {
    target: { value: "Aarav" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  expect(
    await screen.findByRole("heading", { name: "What would you like to do?" }),
  ).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: /Learn something new/ }));
  expect(
    screen.getByRole("button", { name: /Learn something new/ }),
  ).toHaveAttribute("aria-pressed", "true");
});

test("renders the home shell after completing onboarding", async () => {
  renderApp("/signup");
  fireEvent.change(await screen.findByLabelText("Email address"), {
    target: { value: "home@example.com" },
  });
  fireEvent.change(screen.getByLabelText("Password"), {
    target: { value: "long-enough-password" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Create account" }));
  fireEvent.change(await screen.findByLabelText("What should we call you?"), {
    target: { value: "Meera" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  fireEvent.click(
    await screen.findByRole("button", { name: /Learn from my own materials/ }),
  );
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  fireEvent.click(await screen.findByRole("button", { name: "Take me home" }));
  await waitFor(() =>
    expect(screen.getByRole("heading", { name: "Home" })).toBeInTheDocument(),
  );
  expect(screen.getByText(/Meera\./)).toBeInTheDocument();
  expect(screen.getByText("Start your streak today")).toBeInTheDocument();
  expect(screen.getByText("0")).toBeInTheDocument();
  expect(screen.queryByText("Wednesday, 12 November")).not.toBeInTheDocument();
  expect(screen.queryByText(/sessions/)).not.toBeInTheDocument();
  expect(
    screen.getByText("No progress to show yet.", { exact: false }),
  ).toBeInTheDocument();
});

test("defaults to the system theme when no theme is stored", async () => {
  window.matchMedia = (query) =>
    ({ matches: query === "(prefers-color-scheme: dark)" }) as MediaQueryList;
  renderApp("/signup");
  fireEvent.change(await screen.findByLabelText("Email address"), {
    target: { value: "theme@example.com" },
  });
  fireEvent.change(screen.getByLabelText("Password"), {
    target: { value: "long-enough-password" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Create account" }));
  fireEvent.change(await screen.findByLabelText("What should we call you?"), {
    target: { value: "Theme Student" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  fireEvent.click(
    await screen.findByRole("button", { name: /Learn something new/ }),
  );
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  fireEvent.click(await screen.findByRole("button", { name: "Take me home" }));
  await waitFor(() =>
    expect(document.documentElement.dataset.theme).toBe("dark"),
  );
  expect(localStorage.getItem("edusphere-theme")).toBe("dark");
});

test("searches the library and explains an empty result", async () => {
  renderApp("/signup");
  fireEvent.change(await screen.findByLabelText("Email address"), {
    target: { value: "library@example.com" },
  });
  fireEvent.change(screen.getByLabelText("Password"), {
    target: { value: "long-enough-password" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Create account" }));
  fireEvent.change(await screen.findByLabelText("What should we call you?"), {
    target: { value: "Aarav" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  fireEvent.click(
    await screen.findByRole("button", { name: /Learn from my own materials/ }),
  );
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  fireEvent.click(await screen.findByRole("button", { name: "Take me home" }));
  await waitFor(() =>
    expect(screen.getByRole("heading", { name: "Home" })).toBeInTheDocument(),
  );
  fireEvent.click(screen.getAllByRole("link", { name: /Library/ })[0]);
  expect(
    await screen.findByRole("heading", { name: "Find the thread." }),
  ).toBeInTheDocument();
  expect(
    await screen.findByText("Your library is ready for its first PDF."),
  ).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Search your materials"), {
    target: { value: "cellular respiration" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Search" }));
  expect(
    await screen.findByRole("heading", { name: "No matching passages yet." }),
  ).toBeInTheDocument();
  fireEvent.change(
    screen.getByRole("textbox", { name: "Ask your materials" }),
    {
      target: { value: "How do cells convert glucose into energy?" },
    },
  );
  fireEvent.click(screen.getByRole("button", { name: "Ask" }));
  expect(
    await screen.findByText("Chat requires the running backend."),
  ).toBeInTheDocument();
});
