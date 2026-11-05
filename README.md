# AI Visibility Intelligence Platform

Finds the questions people ask AI assistants in a business's market, checks whether the business appears in the answers, ranks the questions by opportunity, and recommends content to close the gaps.

- **Backend:** Flask, SQLAlchemy, Flask-Migrate, three AI agents
- **Frontend:** Angular 21, Angular Material, ng2-charts

## Setup

**API key:** copy `backend/.env.example` to `backend/.env` and set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`. With neither, the app still runs in offline demo mode. Results then come from rule-based templates, and the UI labels them as demo results.

### Docker

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

Open http://localhost:4200. The API is on http://localhost:5000.

### Without Docker

Needs Python 3.11+ and Node 22.12+. Use two terminals.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask --app wsgi db upgrade
flask --app wsgi run --port 5000
```

```bash
cd frontend
npm install
npx ng serve
```

**macOS:** AirPlay Receiver often holds port 5000. If the API won't start, turn it off under System Settings > General > AirDrop & Handoff.

### Tests

```bash
cd backend && pytest
```

```bash
cd frontend && npx ng test --watch=false
```

## Architecture

```
Angular dashboard ── HTTP/JSON ──> Flask blueprints ──> PipelineOrchestrator
                                         │                 │
                                         │                 ├─ QueryDiscoveryAgent
                                     SQLAlchemy            ├─ VisibilityScoringAgent (up to 5 in parallel)
                                         │                 └─ ContentRecommendationAgent
                                      SQLite                         │
                                                        LLM client: Anthropic | OpenAI | offline
```

`POST /run` creates a run, starts it on a background thread and returns 202. The dashboard polls `GET /runs/{uuid}` every 2 seconds. Agents never touch the database. They take plain inputs and return validated objects, and only the orchestrator writes. Worker threads make LLM calls only.

### Agents

All three extend `BaseAgent`, which sends the prompt, pulls JSON from the reply (also handling code fences and surrounding text), and validates it with a Pydantic schema. If that fails, it retries once and tells the model what was wrong. After that it raises `AgentError`, so bad LLM output never crashes the app.

| Agent | Input | Output | Extra validation |
|---|---|---|---|
| Query Discovery | Business profile | 10 to 20 questions | Removes duplicates, retries if under 10, trims to 20 |
| Visibility Scoring | Question and industry | Brands named in the answer, volume, difficulty | Ranges enforced; position worked out in code |
| Content Recommendation | Top 10 queries where the business is missing | 3 to 5 recommendations | Must reference a query it was given; allowed values only |

**The scoring agent isn't told the target brand.** It answers the question, lists the brands it named, and code then looks for the target by domain or name. Naming the brand in the prompt would nudge the model toward mentioning it.

### Partial failures

| What fails | Result |
|---|---|
| Discovery | Run is `failed`, with the reason |
| Some scoring calls | Run is `completed`; those queries stay `unknown`; `error_message` gives the count |
| All scoring calls | Run is `failed`; the queries are kept as `unknown` |
| Recommendations | Run is `completed`; scores are kept; `error_message` explains |
| Server restart mid-run | The run is marked `failed` when someone next starts a run on that profile, once it's over 15 minutes old |

The API shows results from the newest finished run that produced queries, so a failed re-run doesn't hide earlier results.

### Opportunity score

```
demand = log10(volume + 1) / log10(100001)     capped at 100,000 searches
ease   = 1 - difficulty / 100
gap    = 1.0                                   not in the answer
         min(0.1 + 0.15 × (position - 1), 0.7) in the answer

score  = (0.55 × demand + 0.45 × ease) × gap
```

- **Volume is on a log scale** so one huge head term doesn't push every other query close to zero.
- **Demand counts slightly more than ease**, since a hard query with real demand is usually worth more than an easy one nobody asks.
- **Gap multiplies the rest**, so already ranking first scores low however large the query is. Being absent always outranks being present, because the cap is 0.7.

### Model choice

The default is `claude-opus-5-5` at low effort. Each task is short and structured, so low effort keeps cost and time down. Anthropic's server-side fallback is on, so a refused request is retried on another model. Set `LLM_PROVIDER=openai` to use `gpt-4o`. `ANTHROPIC_MODEL` and `OPENAI_MODEL` override the model.

## API

All responses are JSON. Errors always look like this:

```json
{ "error": { "code": "validation_error", "message": "The request is not valid.", "details": [{ "field": "domain", "message": "..." }] } }
```

| Method and path | Purpose | Success |
|---|---|---|
| `POST /api/v1/profiles` | Create a profile | 201 |
| `GET /api/v1/profiles/{uuid}` | Get a profile and its latest run | 200 |
| `POST /api/v1/profiles/{uuid}/run` | Start the pipeline (409 if one is running) | 202 |
| `GET /api/v1/profiles/{uuid}/queries` | `min_score`, `status`, `page`, `per_page` | 200 |
| `GET /api/v1/profiles/{uuid}/recommendations` | List recommendations | 200 |
| `POST /api/v1/queries/{uuid}/recheck` | Re-check visibility (502 if the LLM fails) | 200 |

Added because the dashboard needs them:

| Method and path | Purpose |
|---|---|
| `GET /api/v1/profiles` | List profiles, so a profile with no runs can still be opened |
| `GET /api/v1/runs/{uuid}` | Run status, for polling |
| `GET /api/v1/dashboard/summary` | Totals and recent runs |

## Tradeoffs

- **Search volume is an LLM estimate.** No search data provider is connected, so treat these as rough. The scoring agent is the place to plug in real data.
- **Visibility is one simulated answer.** The model answers from its own knowledge, not by checking live ChatGPT or Perplexity. Answers vary, so a real product would sample several times per assistant.
- **Recheck updates visibility only.** It keeps the earlier volume and difficulty, so a score change always means visibility changed. Existing recommendations are not regenerated.
- **Background thread instead of a job queue.** Simple to run, but a restart loses active runs and it needs a single worker. Celery or RQ would be the next step.
- **SQLite by default.** Fine for one writer here. Set `DATABASE_URL` to use PostgreSQL.
- **The API URL is fixed at build time**, as the assessment's `environment.ts` specifies.

## Notes on the frontend

- Uses Angular's `@if` and `@for` in place of `*ngIf` and `*ngFor`. They do the same job and are the current syntax.
- Uses `@angular/animations` for route transitions, as the brief asks. Angular has marked that package as deprecated in favour of newer APIs.
- `frontend/.npmrc` sets `legacy-peer-deps` because npm 10 crashes resolving `ng2-charts`' open-ended Angular peer range. `package-lock.json` pins the versions.

## AI tools used
