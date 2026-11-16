import "@testing-library/jest-dom";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

// Node 25 shadows jsdom storage with its experimental, incomplete global.
const storage = new Map<string, string>();
vi.stubGlobal("localStorage", {
  getItem: (key: string) => storage.get(key) ?? null,
  setItem: (key: string, value: string) => storage.set(key, String(value)),
  removeItem: (key: string) => storage.delete(key),
  clear: () => storage.clear(),
});
vi.stubGlobal(
  "scrollTo",
  vi.fn(() => Promise.resolve()),
);
afterEach(cleanup);
