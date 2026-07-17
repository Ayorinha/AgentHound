# AgentHound Backend (Phase 1 + Phase 2 + Phase 3)

FastAPI service that ingests a multiagent architecture description (YAML),
normalizes it into a graph-based internal representation (IR), runs a rules
engine to detect capability-based attack paths, scores the findings, and returns
results the frontend can render — then recommends and simulates mitigating
controls.

This implements **Phase 1 + Phase 2 + Phase 3** of the backend
specification: the generic YAML parser, the real
CrewAI/Dify/LangGraph adapters, the IR, the NetworkX graph, rules
**FH-001 / FH-002 / FH-003 / FH-006 / FH-010 / FH-011 / FH-014**, scoring, the
read endpoints, the control catalog, the control recommender and simulator, and
the `/controls/recommendations` and `/simulate-controls` endpoints.

## Pipeline

```
YAML → IR → graph → rules → findings → controls → simulated graph
```

`core/pipeline.py` wires the stages: `parser` → `ir.normalizer` (safe defaults) →
`ir.validators` → `graph.builder` (NetworkX) → `rules.engine` → `storage`. It is
split across two endpoints: `POST /analyses` runs `parse_text` (up to `storage`,
no rules); `POST /analyses/{id}/analyze` runs the rule engine over the stored (or
edited) graph and overwrites the analysis.

## Requirements

- Python 3.11+
- Dependencies: fastapi, uvicorn, pydantic v2, networkx, pyyaml, python-multipart
  (dev: pytest, httpx)

## Run locally

```bash
# from Backend/
python -m venv .venv
. .venv/bin/activate            # Linux/macOS
# .venv\Scripts\Activate.ps1    # Windows (PowerShell)
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Interactive API docs are served at `http://127.0.0.1:8000/docs` (Swagger) and
`/redoc` (ReDoc). Health check at `/health`.

## Run with Docker

```bash
# from Backend/
docker build -t agenthound-backend .
docker run -p 8000:8000 -v "$PWD/data:/data" agenthound-backend
```

## Test

```bash
# from Backend/
pytest
```

## Try it

```bash
curl -F "file=@tests/fixtures/hiresmart_generic.yaml" http://127.0.0.1:8000/analyses
# -> {"analysis_id": "...", "status": "parsed", "summary": {...}}  (no findings yet)
curl -X POST http://127.0.0.1:8000/analyses/<analysis_id>/analyze   # runs the rules
curl http://127.0.0.1:8000/analyses/<analysis_id>/graph
curl http://127.0.0.1:8000/analyses/<analysis_id>/findings
curl http://127.0.0.1:8000/analyses/<analysis_id>/controls/recommendations
curl -X POST http://127.0.0.1:8000/analyses/<analysis_id>/simulate-controls \
  -H "Content-Type: application/json" \
  -d '{"controls_to_apply":[{"control_id":"humanInTheLoop","target_node_id":"output_email_candidate"}]}'
```

## Module map

| Path | Responsibility |
|------|----------------|
| `app/main.py` | FastAPI app factory, routers, error handlers |
| `app/api/routes/` | `analyze`, `graphs`, `findings`, `controls` endpoints |
| `app/api/errors.py` | Spec §13 error envelope helpers |
| `app/core/pipeline.py` | End-to-end orchestration |
| `app/core/parser/` | `yaml_loader` + framework detection, `adapters/` |
| `app/core/ir/` | Pydantic models, `normalizer`, `validators` |
| `app/core/graph/` | `builder` (NetworkX), `traversal`, `serializer` |
| `app/core/rules/` | `engine`, `registry`, `path_rules`, `node_rules`, `scoring` |
| `app/core/controls/` | `recommender`, `simulator` (Phase 2) |
| `app/core/storage/` | In-memory + JSON `repository` |
| `app/catalogs/` | `capabilities`, `node_properties`, `rules`, `controls` YAML |
| `app/docs/` | This documentation set |

## Related docs

- [`api.md`](api.md) — endpoint reference
- [`ir_and_rules.md`](ir_and_rules.md) — IR schema, capabilities, rules, scoring
- [`glossary.md`](glossary.md) — plain-language terms
- [`decisions.md`](decisions.md) — decisions and deferred scope
