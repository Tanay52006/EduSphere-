import { ChangeEvent, FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, EmptyState, Skeleton } from "../components/ui";
import { Link } from "react-router-dom";
import { api, ApiError, type DocumentItem, type SearchHit } from "../lib/api";

function DocumentRow({ document }: { document: DocumentItem }) {
  const status = document.status.replace(/_/g, " ");
  const statusLabel =
    document.status === "failed" ? "Processing failed" : status;
  return (
    <article className="document-row">
      <div className="document-icon" aria-hidden="true">
        PDF
      </div>
      <div className="document-copy">
        <strong>{document.original_filename}</strong>
        <span>
          {document.page_count} {document.page_count === 1 ? "page" : "pages"}
        </span>
      </div>
      <div className={`document-status status-${document.status}`}>
        {document.ocr_required ? "OCR needed" : statusLabel}
        {(document.status === "queued" || document.status === "running") && (
          <span>{document.progress}%</span>
        )}
        {document.status === "ready" && (
          <Link
            className="document-play-link"
            to={`/questions?document=${document.id}`}
          >
            Make it playable ↗
          </Link>
        )}
      </div>
    </article>
  );
}

function SourceBadge({ source }: { source: string }) {
  return <span className={`source-badge source-${source}`}>{source}</span>;
}

function SearchResult({ result }: { result: SearchHit }) {
  return (
    <article className="search-result">
      <div className="search-result-topline">
        <div className="source-list" aria-label="Matched by">
          {result.sources.map((source) => (
            <SourceBadge key={source} source={source} />
          ))}
        </div>
        <span className="result-pages">
          Pages {result.page_start}–{result.page_end}
        </span>
      </div>
      {result.heading && <h3>{result.heading}</h3>}
      <p>{result.text}</p>
      <span className="result-document">
        Document {result.document_id.slice(0, 8)}
      </span>
    </article>
  );
}

export function Library() {
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [question, setQuestion] = useState("");
  const queryClient = useQueryClient();
  const documents = useQuery({
    queryKey: ["documents"],
    queryFn: api.documents,
    refetchInterval: (query) =>
      query.state.data?.some((document) =>
        ["queued", "running"].includes(document.status),
      )
        ? 1500
        : false,
  });
  const upload = useMutation({
    mutationFn: api.uploadDocument,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
  });
  const chat = useMutation({
    mutationFn: (nextQuestion: string) => api.chat(nextQuestion),
  });
  const search = useQuery({
    queryKey: ["search", submittedQuery],
    queryFn: () => api.search(submittedQuery),
    enabled: submittedQuery.length > 0,
    retry: false,
  });

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextQuery = query.trim();
    if (nextQuery) setSubmittedQuery(nextQuery);
  };
  const chooseFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) upload.mutate(file);
    event.target.value = "";
  };

  const errorMessage =
    search.error instanceof ApiError
      ? search.error.message
      : "Search could not be completed. Try again.";

  return (
    <div className="library-content">
      <section className="library-intro">
        <div>
          <p className="eyebrow">Your study materials</p>
          <h2>Find the thread.</h2>
          <p className="lead">
            Search across your notes and PDFs for the idea you want to pick up.
          </p>
        </div>
        <div className="library-mark" aria-hidden="true">
          ⌕
        </div>
      </section>

      <section
        className="materials-section"
        aria-labelledby="materials-heading"
      >
        <div className="materials-heading">
          <div>
            <p className="eyebrow">Your library</p>
            <h3 id="materials-heading">Materials</h3>
          </div>
          <label className="button button-secondary upload-button">
            {upload.isPending ? "Uploading…" : "Add PDF"}
            <input
              type="file"
              accept="application/pdf,.pdf"
              onChange={chooseFile}
              disabled={upload.isPending}
            />
          </label>
        </div>
        {upload.isError && (
          <div className="library-message library-message-error" role="alert">
            {upload.error instanceof ApiError
              ? upload.error.message
              : "Upload could not be completed."}
          </div>
        )}
        {documents.isError && (
          <div className="library-message library-message-error" role="alert">
            Could not load your materials. Try refreshing the page.
          </div>
        )}
        {documents.isSuccess && documents.data.length === 0 && (
          <p className="materials-empty">
            Your library is ready for its first PDF.
          </p>
        )}
        {documents.isSuccess && documents.data.length > 0 && (
          <div className="document-list">
            {documents.data.map((document) => (
              <DocumentRow key={document.id} document={document} />
            ))}
          </div>
        )}
      </section>

      <form className="library-search" onSubmit={submit} role="search">
        <label htmlFor="library-query">Search your materials</label>
        <div className="search-input-row">
          <span className="search-icon" aria-hidden="true">
            ⌕
          </span>
          <input
            id="library-query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Try “how does cellular respiration work?”"
            maxLength={500}
            autoComplete="off"
          />
          <Button
            type="submit"
            disabled={!query.trim()}
            loading={search.isFetching}
          >
            Search
          </Button>
        </div>
        <p className="search-hint">
          Results stay inside your account and include the page they came from.
        </p>
      </form>

      <section className="library-chat" aria-labelledby="chat-heading">
        <div className="results-heading">
          <div>
            <p className="eyebrow">Grounded study help</p>
            <h3 id="chat-heading">Ask your materials</h3>
          </div>
          <span>Answers cite your pages</span>
        </div>
        <form
          className="chat-form"
          onSubmit={(event) => {
            event.preventDefault();
            const nextQuestion = question.trim();
            if (nextQuestion) chat.mutate(nextQuestion);
          }}
        >
          <label htmlFor="library-question">Ask your materials</label>
          <textarea
            id="library-question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask a question about your PDFs"
            maxLength={1000}
            rows={3}
          />
          <Button
            type="submit"
            disabled={!question.trim()}
            loading={chat.isPending}
          >
            Ask
          </Button>
        </form>
        {chat.isError && (
          <div className="library-message library-message-error" role="alert">
            {chat.error instanceof ApiError
              ? chat.error.message
              : "The answer could not be loaded."}
          </div>
        )}
        {chat.isSuccess && (
          <div className="chat-answer" aria-live="polite">
            <p>{chat.data.answer}</p>
            {chat.data.grounded && (
              <div className="chat-citations">
                {chat.data.citations.map((citation) => (
                  <span key={citation.chunk_id}>
                    Pages {citation.page_start}–{citation.page_end}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </section>

      {search.isPending && submittedQuery && (
        <div className="search-results" aria-label="Loading results">
          <Skeleton className="result-skeleton" />
          <Skeleton className="result-skeleton" />
        </div>
      )}

      {search.isError && (
        <div className="library-message library-message-error" role="alert">
          <strong>{errorMessage}</strong>
          <span>Check your connection and try the search again.</span>
        </div>
      )}

      {search.isSuccess && search.data.results.length === 0 && (
        <EmptyState
          icon="⌁"
          title="No matching passages yet."
          action={
            <span className="library-empty-note">
              Try a broader phrase or upload another PDF.
            </span>
          }
        >
          We searched the materials in your library and found nothing for “
          {search.data.query}”.
        </EmptyState>
      )}

      {search.isSuccess && search.data.results.length > 0 && (
        <section className="search-results" aria-live="polite">
          <div className="results-heading">
            <h3>{search.data.results.length} passages found</h3>
            <span>Grounded in your materials</span>
          </div>
          {search.data.results.map((result) => (
            <SearchResult key={result.chunk_id} result={result} />
          ))}
        </section>
      )}

      {!submittedQuery && (
        <div className="library-starter">
          <div className="starter-line" />
          <span>Search becomes useful once your first material is ready.</span>
          <div className="starter-line" />
        </div>
      )}
    </div>
  );
}
