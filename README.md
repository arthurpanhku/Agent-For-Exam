# StudyForge

**StudyForge** is an MIT-licensed study workspace that couples document ingestion, graph-backed retrieval, and optional tool orchestration. It helps learners ground answers in their own PDF/PPTX materials, inspect citations at roughly page level, and run workflows such as practice-paper analysis, cheatsheet drafting, and automated grading pipelines where configured.

This README describes behavior at a high level; deployment specifics appear later.

---

## What you get

- **Structured ingestion**: Upload course packs as PDF or PPTX (limits enforced server-side).
- **Hybrid retrieval**: Vector lookup combined with graph-oriented modes exposed through the API (`naive`, `local`, `global`, `mix`).
- **Traceability**: Answers can surface references tied back to rendered slides/pages when indexing completes.
- **Tool-assisted chat**: Optional function-calling path registers backend capabilities (documents listing, graph queries, mind-map synthesis, paged reads, etc.).
- **Operational tooling**: Docker stacks, local launcher scripts, optional HTTP gateway key, request correlation IDs, and contract tests.

Imagery under `./image/` illustrates layout only; filenames are unchanged for existing docs links.

---

## Architecture (conceptual)

```
Browser (Vue 3) ──► FastAPI ──► extraction / LightRAG adapters ──► local KV + vectors + graph stores
```

The bundled **LightRAG** subtree ships under its **own** `LightRAG/LICENSE` (MIT). StudyForge application code is under this repository’s MIT license unless a file states otherwise.

---

## Requirements

| Context | Needs |
|--------|--------|
| Docker | Docker Engine / Desktop |
| Native dev | Python ≥ 3.10, Node ≥ 16, npm; LibreOffice recommended for crisp PPTX previews locally |

---

## Quick start

### Docker (production-style)

```bash
docker compose up -d
docker compose down
```

- UI (nginx): `http://localhost`
- API: `http://localhost:8000/docs`

Optional root `.env`:

```bash
STUDYFORGE_API_KEY=your-shared-gateway-secret
```

The frontend container template injects this header when proxying `/api/`. Legacy `AFE_API_KEY` is still read by the backend settings layer if you must migrate gradually.

### Docker (live-reload dev stack)

```bash
docker compose -f docker-compose.dev.yml up --build
```

- Vite: `http://localhost:5173`
- API: `http://localhost:8000`

### Native scripts

```bash
chmod +x start_all.sh stop_all.sh
./start_all.sh
```

Windows PowerShell equivalents live beside them. Backend hot reload:

```bash
STUDYFORGE_RELOAD=1 ./start_all.sh   # legacy AFE_RELOAD=1 still honored
```

Manual startup notes: see `backend/README.md` and `frontend/README.md`.

---

## Configuration highlights

1. **LLM credentials & models** — configured through the in-app **Settings** UI (encrypted at rest on the server). OpenAI-compatible SiliconFlow-style endpoints are commonly used; plug in whichever vendor matches your deployment policy.
2. **Gateway key** — set `STUDYFORGE_API_KEY` (or legacy `AFE_API_KEY`) to force `X-API-Key` on every route except `OPTIONS` and `GET /health`. Browser builds may set `VITE_STUDYFORGE_API_KEY` (with fallback to `VITE_AFE_API_KEY`) when calling the API directly—prefer reverse-proxy injection for sensitive deployments.
3. **Tracing** — responses may include `request_id` alongside the `X-Request-ID` header; unexpected failures return a generic `detail` while specifics stay in logs.

---

## Testing

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

See `backend/tests/test_api_contracts.py` for smoke coverage.

---

## Repository layout

```
studyforge/
├── backend/           FastAPI services
├── frontend/          Vue 3 + Vite client
├── LightRAG/          Upstream LightRAG sources (see LightRAG/LICENSE)
├── docs/              Feature notes & deep dives (incl. dataset description & evaluation plan)
├── scripts/           Operational helpers
├── docker-compose*.yml
└── start_all.* / stop_all.*
```

---

## Dataset description & evaluation plan

For coursework or technical memos that require explicit **dataset documentation** and an **evaluation playbook**:

- **Canonical Markdown**: [`docs/DATASET_AND_EVALUATION.md`](docs/DATASET_AND_EVALUATION.md) (English: corpus scope, metadata checklist, phased metrics, milestones).
- **In-app**: open **Dataset & Evaluation** in the sidebar (route `/dataset-evaluation`) for the same Markdown, plus editors for **per-subject dataset descriptions** (also editable on each subject’s Documents page).

---

## Repository

- **GitHub**: [https://github.com/arthurpanhku/studyforge](https://github.com/arthurpanhku/studyforge)

```bash
git clone https://github.com/arthurpanhku/studyforge.git
cd studyforge
```

---

## License

StudyForge application sources are released under the **MIT License** (`LICENSE` in the repo root).

Third-party components retain their original notices (notably **LightRAG** under `LightRAG/LICENSE`). Include both licenses when redistributing bundles.

---

## Contributing

Issues and pull requests are welcome. Keep derivative documentation clearly attributed and respect upstream licenses when modifying vendored trees.
