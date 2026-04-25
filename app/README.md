# COBAI Application

This folder contains the runnable MVP for the COBOL learning agent.

## Modes

- `coach`: interactive learning mode with the guardrailed COBOL assistant
- `study`: structured research mode with fixed participant flow
- `list-modules`: quick content inventory

## Files

- `study_runner.py` - CLI entry point
- `coach.py` - lesson-aware COBOL coach wrapper
- `llm_client.py` - Ollama-compatible Responses API client
- `config.py` - settings and secret loading
- `env_loader.py` - `.env` file support for ignored local configs
- `content_loader.py` - lesson and tutorial loading
- `scoring.py` - multiple-choice scoring helpers
- `export_results.py` - CSV and JSONL append logic

## Local LLM Settings

- The default API endpoint is `http://localhost:11434/v1`.
- The default model is `qwen2.5-coder:7b`.
- The default API key is `ollama`, which Ollama requires for compatibility but ignores.
- `.env` and `app/.env` are supported and gitignored.
- The app never exports the API key to result files.
