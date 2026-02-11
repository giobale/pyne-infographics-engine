# SalesBanana

AI-powered diagram generation pipeline. Takes a natural-language brief and produces a styled, brand-consistent diagram image through a multi-agent pipeline with iterative refinement.

## Architecture

```
Brief (text)
  |
  v
Retriever  -->  Planner  -->  Stylist  -->  Visualizer  <-->  Critic
(classify)     (describe)    (style)      (generate)        (evaluate)
  |                                            |
  v                                            v
refs.json                                  final.png
+ images/
```

**Phase 1 — Planning** (linear): Retriever classifies the brief and selects reference images. Planner generates a visual description. Stylist applies brand directives.

**Phase 2 — Refinement** (iterative): Visualizer generates the image. Critic evaluates it. If not approved, the critic returns a refined description and the loop repeats (up to `MAX_REFINEMENT_ROUNDS`).

## Components

| Directory | Role | Details |
|-----------|------|---------|
| [`src/agents/`](src/agents/README.md) | Five pipeline agents (retriever, planner, stylist, visualizer, critic) | Each wraps a single OpenAI API call |
| [`src/utils/`](src/utils/README.md) | Shared helpers (image encoding, prompt loading) | No business logic |
| [`config/`](config/README.md) | Prompt templates and brand style guide | The main customization surface |
| [`references/`](references/README.md) | Example diagrams used as few-shot visual context | Add your own PNGs here |

## Key files

| File | Purpose |
|------|---------|
| `src/config.py` | Settings singleton (loaded from `.env`), OpenAI client |
| `src/pipeline.py` | Orchestrator — wires agents, manages refinement loop |
| `src/models.py` | Pydantic data models (`PipelineResult`, `CriticOutput`, etc.) |
| `main.py` | CLI entry point |
| `app.py` | Web UI (FastAPI) |

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your OPENAI_API_KEY
```

## Usage

**CLI:**
```bash
python main.py "A pipeline showing data flowing from Stripe through ETL into Snowflake"
```

**Web UI:**
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
# Open http://localhost:8000
```

## Configuration

All settings are in `.env`. See `.env.example` for defaults.

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | — | Required |
| `LLM_MODEL` | `gpt-4o` | Text agents |
| `IMAGE_MODEL` | `gpt-image-1` | Image generation |
| `MAX_REFINEMENT_ROUNDS` | `3` | Visualizer-critic loop limit |
| `NUM_REFERENCES` | `5` | Reference images per run |

## Output

Each run creates a timestamped directory in `output/`:

```
output/YYYYMMDD_HHMMSS/
  01_retriever_refs.json
  02_planner_description.md
  03_stylist_description.md
  04_round_N_image.png
  04_round_N_critique.md
  final.png
  run_metadata.json
```
