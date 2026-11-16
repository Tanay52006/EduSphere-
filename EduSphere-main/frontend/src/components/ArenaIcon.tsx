import type { ReactNode } from "react";

const shapes = {
  home: (
    <>
      <path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1Z" />
    </>
  ),
  library: (
    <>
      <path d="M4 4h4v16H4zm6 0h4v16h-4zm6 1 4-1 3 15-4 1z" />
    </>
  ),
  paths: (
    <>
      <circle cx="6" cy="5" r="2" />
      <circle cx="18" cy="19" r="2" />
      <path d="M8 5h7a4 4 0 0 1 0 8H9a3 3 0 0 0 0 6h7" />
    </>
  ),
  games: (
    <>
      <path d="M7 7h10a4 4 0 0 1 4 3l1 7a2 2 0 0 1-3 2l-4-3H9l-4 3a2 2 0 0 1-3-2l1-7a4 4 0 0 1 4-3Z" />
      <path d="M6 11v4m-2-2h4m8-2h.01m3 3h.01" />
    </>
  ),
  progress: (
    <>
      <path d="M4 20V10m8 10V4m8 16v-7" />
      <path d="M2 20h20" />
    </>
  ),
  bolt: <path d="m14 2-10 12h7l-1 8L20 9h-7z" />,
  cards: (
    <>
      <rect x="8" y="6" width="12" height="15" rx="2" />
      <path d="M5 17H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2" />
      <path d="m11 13 3-3 3 3-3 3z" />
    </>
  ),
  play: <path d="m9 5 11 7-11 7z" />,
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </>
  ),
  heart: (
    <path d="M20.5 4.5a5 5 0 0 0-7 0L12 6l-1.5-1.5a5 5 0 0 0-7 7L12 20l8.5-8.5a5 5 0 0 0 0-7Z" />
  ),
  flame: (
    <path d="M12 2c1 5 7 7 7 13a7 7 0 0 1-14 0c0-3 2-6 4-7 0 4 2 5 3 4 2-2 0-5 0-10Z" />
  ),
  target: (
    <>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <circle cx="12" cy="12" r="1" />
    </>
  ),
  trophy: (
    <>
      <path d="M8 3h8v6a4 4 0 0 1-8 0Zm0 2H4v3a4 4 0 0 0 4 4m8-7h4v3a4 4 0 0 1-4 4m-4 1v5m-4 3h8m-6-3h4v3h-4z" />
    </>
  ),
  shield: (
    <>
      <path d="m12 2 8 4v6c0 5-8 10-8 10S4 17 4 12V6Z" />
      <path d="m8 12 3 3 5-6" />
    </>
  ),
  lock: (
    <>
      <rect x="5" y="10" width="14" height="11" rx="2" />
      <path d="M8 10V7a4 4 0 0 1 8 0v3m-4 5v2" />
    </>
  ),
  check: <path d="m5 12 4 4L19 6" />,
  arrow: <path d="M4 12h16m-6-6 6 6-6 6" />,
  sun: (
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1 1m12 12 1 1M5 19l1-1M18 6l1-1" />
    </>
  ),
  moon: <path d="M20 14A9 9 0 0 1 10 3a9 9 0 1 0 10 11Z" />,
} satisfies Record<string, ReactNode>;

export type ArenaIconName = keyof typeof shapes;

export function ArenaIcon({
  name,
  size = 24,
}: {
  name: ArenaIconName;
  size?: number;
}) {
  return (
    <svg
      className="arena-icon"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {shapes[name]}
    </svg>
  );
}
