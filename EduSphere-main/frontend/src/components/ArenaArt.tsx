import { ArenaIcon } from "./ArenaIcon";

// The previews show each game's interaction instead of unrelated decoration.
export function ArenaArt({ memory = false }: { memory?: boolean }) {
  return (
    <div
      className={`game-art ${memory ? "memory-art" : "quiz-art"}`}
      aria-hidden="true"
    >
      {memory ? (
        <div className="match-preview">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <span
              key={i}
              className={i === 1 || i === 4 ? "preview-matched" : ""}
            >
              {i === 1 || i === 4 ? (
                <ArenaIcon name="target" size={30} />
              ) : (
                <span className="deck-mark" />
              )}
            </span>
          ))}
          <i className="preview-connection">
            <ArenaIcon name="check" size={16} />
          </i>
        </div>
      ) : (
        <div className="blitz-preview">
          <div className="preview-time">
            <ArenaIcon name="clock" size={14} />
            <span>00:30</span>
            <span className="preview-time-track" />
          </div>
          <div className="preview-prompt">
            <span />
            <span />
          </div>
          <div className="preview-answers">
            {["A", "B", "C", "D"].map((letter, i) => (
              <span
                key={letter}
                className={i === 1 ? "preview-answer-selected" : ""}
              >
                <b>{letter}</b>
                <i />
                {i === 1 && <ArenaIcon name="check" size={14} />}
              </span>
            ))}
          </div>
        </div>
      )}
      <span className="art-mode-number">{memory ? "02" : "01"}</span>
    </div>
  );
}
