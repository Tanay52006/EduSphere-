# 04. Design system

**Direction: "Notion's calm, with colour."** Notion's restraint (quiet chrome, content-first, lots of whitespace, a blocks-and-pages feel) with a vibrant accent system so it never reads as grey. Colour appears in meaningful places, such as subjects, games, progress and rewards, not as decoration. All values are starting points to be refined by the `impeccable` skill in Phase 1, which should output `DESIGN.md`.

## Principles
1. Content first; chrome whispers, rewards sing.
2. Colour carries meaning: each game and each subject owns a colour pair.
3. Warm, not sterile: warm off-white surfaces, soft borders, gentle radii.
4. Delight is brief: celebrate wins in ~600 ms and then get out of the way. Always honour `prefers-reduced-motion`.
5. Accessible by default: contrast ≥ 4.5:1 for text, visible focus rings, full keyboard support, semantic HTML.

## Typography
- UI and body: **Inter** (variable), with the system-ui stack as fallback; 15–16 px base, 1.5 line height; tabular numbers for XP and scores.
- Display moments (onboarding headline, level-up, path title): a friendly editorial serif such as **Newsreader** at large sizes. **[my call]** Replace it if `impeccable` finds a better pairing.
- Scale: 12 / 14 / 16 / 20 / 24 / 32 / 44. Headings are medium or semibold, not bold. Notion-like title blocks: big, left-aligned, generous spacing.

## Colour tokens (CSS variables; every token has a dark-mode counterpart)
Neutrals (light): `--bg #FFFFFF`, `--surface #FBFBFA`, `--hover rgba(55,53,47,.06)`, `--border rgba(55,53,47,.09)`, `--text #37352F`, `--muted #787774`.
Neutrals (dark): `--bg #191919`, `--surface #202020`, `--text #EBEBEA`, `--border rgba(255,255,255,.09)`.

**Accent families.** Each family has `soft` (tag background), `ink` (text on soft), `solid` (CTA/game moments) and `solid-ink`. Modelled on Notion's tag palette, with saturated solids.

| Family | Soft | Ink | Solid | Used for |
|---|---|---|---|---|
| Blue | `#D3E5EF` | `#183347` | `#2383E2` | Primary actions, links, Path B |
| Green | `#DBEDDB` | `#1C3829` | `#2EAB6F` | Success, correct, progress |
| Yellow | `#FDECC8` | `#402C1B` | `#F2B31B` | XP, streak, rewards |
| Orange | `#FADEC9` | `#49290E` | `#F2742C` | Streak flame, warnings |
| Pink | `#F5E0E9` | `#5B2245` | `#E255A1` | Memory Match, badges |
| Purple | `#E8DEEE` | `#412454` | `#8B5CF6` | Path A, Brain Ladder |
| Red | `#FFE2DD` | `#5D1715` | `#E5484D` | Errors, wrong answers |
| Teal | `#D6EEEA` | `#134340` | `#12A594` | Hangman, info |

Rules: one solid accent per screen region; soft fills for tags and cards; semantic colours (green = right, red = wrong, yellow = reward) are never reused decoratively.

## Shape, depth, spacing
- Radii 6 / 10 / 16. Borders over shadows; a single soft shadow for popovers and drag states.
- 4 px spacing grid; content column ~720 px for reading, wide layout for games and dashboards.
- Notion-like left sidebar (collapsible; bottom tab bar on mobile): Home, Library, Paths, Games, Progress.

## Components (build in Phase 1, extend later)
Button (primary/secondary/ghost/destructive), input and textarea, select, checkbox/switch, tag, card, callout, progress bar and ring, tabs, tooltip, modal/sheet, toast, menu, skeleton, empty state, avatar. Gamification components: XP chip, level ring, streak flame, badge tile, confetti burst (tiny, canvas-free).

## Motion
Tokenised durations (120 / 200 / 320 ms) and easings. Use opacity and transform only. Micro-interactions: press scale 0.97, tag hover lift, correct-answer pop, progress fill. Level-up and badge earned get the one big moment. Respect reduced motion by replacing with fades.

## States (required on every feature)
Hover, focus-visible, active, disabled, loading (skeletons, not spinners, for content), empty (with a clear next action), success, error (human language, retry).

## Onboarding feel
Full-width calm screens, large serif headline, two large choice cards for the fork. Each card has its own accent (purple = own materials, blue = new topic), a soft illustration or glyph, and one line of promise. Progress dots, Back always available, no dead ends.

## Responsive
Mobile first. Breakpoints 640 / 1024. Games must be playable one-handed on a phone.

## Review checklist
Rendered in a browser at 3 widths, light and dark, keyboard-only pass, reduced-motion pass, contrast check, no layout shift.

## Current Phase 3 game direction (13 November 2026)

The contributor's latest instruction is to build on the existing app UI and focus on good games. Games and Chain Reaction reuse the app shell, sidebar, bottom navigation, theme tokens, buttons and feedback patterns. A compact chapter card sits above personal-PDF practice. Generated biology illustrations explain stations on the playable board; the separate planet header, island map and decorative guide have been removed. Home, Library and Progress retain their existing UI. See [Chain Reaction](10-chain-reaction.md) for interaction and verification.
