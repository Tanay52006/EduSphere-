# Rive motion integration

**Deferred following the contributor's latest instruction to retain the existing app UI and focus on games.** No authored `.riv` file or Rive runtime is shipped. The removed island/guide design below is historical planning, not the current visual target. React's scene phases remain available, and the current board uses brief CSS connection flow with reduced-motion support.

## Ownership

React owns controls, responsive station positions, selected ports and the request lifecycle. FastAPI owns correctness, completion and XP. Rive will render the guide and decorative feedback; it must never award XP, decide whether a pathway is valid, navigate, or block the next action while an animation finishes. The dynamic connection geometry stays in the existing accessible DOM/SVG board rather than being duplicated in an animation file.

Use the official React WebGL2 runtime with its hooks and bound View Model. Rive currently documents `@rive-app/react-webgl2`, `useRive`, `autoBind` and a singular `stateMachine` option. Pin and verify the installed version when the first authored file is available, rather than installing an unused runtime now. [Official React runtime](https://rive.app/docs/runtimes/react/react).

## One scene, coordinated reactions

Author `edusphere-guide.riv` with `Guide` artboard, `GuideMotion` state machine and `GameScene` View Model. Retain the approved coral gecko and its palette. Separate head, eyelids, pupils, waving arm, body, tail and environment layers in the Rive source; the generated single bitmap is a reference/static fallback, not an automatically editable character rig.

| Game event | Shared phase | Guide / effects | Duration target |
| --- | --- | --- | --- |
| Enter an unfinished puzzle | `idle` | Static attentive pose; occasional blink, no continuous bouncing | Blink occasionally |
| Select an output | `connecting` | Eyes/head turn toward the board; chosen port remains React-controlled | 120–180 ms |
| Connect two ports | `connecting` | One small acknowledgement; no green success claim | 150 ms |
| Press Run / request pending | `running` | Guide watches; no completion or XP animation yet | Until response |
| Server rejects route | `retry` | Small curious head tilt; stop at the server-reported broken link | 250–350 ms |
| Server confirms completion | `success` | Energy flows first, cell responds next, guide celebrates last; one small confetti burst | 700–1000 ms total |
| Load an already completed round | `complete` | Hold the final pose; show saved XP, do not replay celebration | Static |
| Undo or edit | `idle` / `connecting` | Cancel previous transient reaction and return to attentive pose | 120 ms |

`ChainRound` already supplies the authoritative scene phase as `data-motion` and a per-run `data-motion-revision`. The future React Rive wrapper should receive these same values directly as props, without polling DOM attributes or inventing a second gameplay state machine. A restored completed round has revision zero and phase `complete`; a fresh acknowledged completion has `success` with an incremented revision.

View Model contract: `phase` enum with the six values above; `selectedStation` string; `reducedMotion` boolean; `reaction` trigger fired once per new acknowledged run. The phase distinguishes a saved result from a fresh celebration. Use current View Model property hooks; bindings and transitions are authored inside the Rive file. [Official data binding](https://rive.app/docs/runtimes/react/data-binding).

Use separate overlay artboards only if the guide file needs a cell response or confetti. Their initial frame must be transparent. Keep the game board and controls visible during loading. Only one character reaction should compete for attention at once: a retry is a subtle cue, and the bigger success moment happens after the pathway finishes its brief pulse.

## Runtime behaviour and acceptance

- Lazy-load the runtime and self-host the `.riv` and matching WASM asset. Keep a static generated WebP in the same fixed-size box while loading or after any load/WebGL error. A loading failure must not interrupt a round.
- Treat Rive as decorative: canvas `aria-hidden`, pointer events disabled, HTML buttons and source links remain accessible and labelled. No external URL events or sound autoplay.
- For reduced motion, display the corresponding static pose and final pathway colours immediately. Pause off-screen and while the document is hidden; clean up instances on unmount. Do not create a new instance for every link change.
- Drive playback through the runtime's play/pause controls. Rive documents paused and settled state machines, including their performance behaviour. [Official playback controls](https://rive.app/docs/runtimes/react/state-machines).
- Cap canvas device pixel ratio at 2 initially. Measure on a real lower-end phone before increasing quality or allowing more than two active artboards. Keep layout dimensions stable to avoid jumps.
- Test pending → retry → edit → pending → success; rapid repeated Run; resize mid-connection; result reload; hidden-tab pause; reduced motion; failed `.riv`/WASM load; and WebGL loss. XP and progression must remain unchanged by playback, failure or replay.

Remaining production work: author and export the faithful character rig in Rive, connect the View Model through the runtime wrapper, then run the acceptance sequence above. Do not substitute an unrelated community mascot or label CSS motion as Rive.
