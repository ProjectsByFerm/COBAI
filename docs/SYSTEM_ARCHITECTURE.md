# COBAI System Architecture

## Goal

COBAI is a simple local prototype for presenting COBOL learning materials,
running a guardrailed LLM explanation flow, collecting study responses, and
exporting results for analysis.

The system wraps a local Ollama model API. It does not train a model.

## MVP Stack

- Language: Python
- Interface: command-line runner
- LLM: Ollama-compatible Responses API
- Storage: CSV and JSONL local files
- Config: shell environment variables or ignored `.env` files
- Analysis: lightweight Python summary script

## Core Components

### Study Runner

Responsible for:

1. loading a module
2. assigning or accepting a condition
3. collecting participant inputs
4. showing lesson material
5. running the timed task
6. exporting results

### Guardrailed Coach

Responsible for:

- loading the fixed prompt guardrails
- injecting lesson context
- keeping responses beginner-friendly
- preventing answer leakage during locked assessments

### Content Files

Stored outside the app code:

- lesson modules
- static tutorials
- prompt guardrails

### LLM Client

Responsible for:

- sending requests to the local Ollama API
- sending developer and user prompts
- recording latency and response metadata
- returning the generated explanation text

### Export Layer

Responsible for:

- appending JSONL session data
- appending CSV summaries
- keeping the schema stable across runs

## Data Flow

Static condition:

```text
Participant
  -> Study Runner
  -> Static Tutorial
  -> Answers and Timing
  -> CSV/JSONL Results
```

LLM condition:

```text
Study Runner
  -> Guardrail Prompt + Lesson Context + COBOL Snippet
  -> LLM API Client
  -> Local Ollama API
  -> Generated Explanation
  -> Participant
  -> CSV/JSONL Results
```

## Repo Structure

```text
app/
analysis/
data/
docs/
materials/
protocol/
```

## Secret Handling

Default local model settings:

- `LLM_API_BASE_URL=http://localhost:11434/v1`
- `LLM_API_KEY=ollama`
- `LLM_MODEL=qwen2.5-coder:7b`

Ignored local config files:

- `.env`
- `.env.*`
- `app/.env`
- `app/.env.*`
