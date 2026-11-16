# Groq Provider Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Add a configuration-driven Groq generation adapter while preserving Gemini embeddings for RAG retrieval.

**Architecture:** Implement Groq over the existing `httpx` dependency using Groq's OpenAI-compatible chat-completions endpoint. `generate_text` and `generate_json` use Groq; `embed` delegates to the existing Gemini embedding adapter, with a clear configuration error if the Gemini embedding credential is absent.

**Tech Stack:** FastAPI provider boundary, `httpx`, Pydantic validation, pytest, existing Gemini adapter.

**Spec:** User request to add Groq as an LLM provider without weakening grounded retrieval.

## Global Constraints

- No credentials in source, fixtures, logs, or responses.
- Provider and model names come from configuration.
- Every generated answer remains schema-validated by the existing chat route.
- Retrieval embeddings remain available and user-scoped.
- Do not edit or execute `References/`.
- Do not add a dependency when the existing permissive `httpx` dependency is sufficient.

## Review Focus

- Groq JSON responses must be parsed and validated by the existing boundary.
- HTTP errors and malformed responses must fail safely.
- Groq generation must not silently replace embeddings with fabricated vectors.
- Missing Gemini embedding credentials must produce a configuration error before serving requests.
- Factory selection must remain compatible with mock, Ollama, Gemini, and Vertex.

### Task 1: Add the Groq adapter

- [x] Add mocked-transport tests for text, JSON, HTTP errors, malformed JSON, and Gemini-backed embeddings.
- [x] Run the focused tests and verify they fail because the adapter does not exist.
- [x] Implement `GroqProvider` using `httpx.AsyncClient` and configuration values.
- [x] Run focused tests and verify they pass.

### Task 2: Wire configuration and factory selection

- [x] Add Groq settings and safe defaults to `Settings` and `.env.example`.
- [x] Add factory selection and tests for `groq`.
- [x] Run config and factory tests.

### Task 3: Document and verify

- [x] Record the Groq-generation/Gemini-embedding decision and dependency/license rationale.
- [x] Run the full `make check` suite.
- [ ] Run a provider smoke test without printing credentials.
- [ ] Commit and push the branch.
