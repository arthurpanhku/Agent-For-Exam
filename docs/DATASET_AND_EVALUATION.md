# StudyForge — Dataset Description & Evaluation Plan

This document supports course projects, research deliverables, and engineering handoffs. It explains what “dataset” means inside StudyForge, how to record provenance, and how to plan evaluations for retrieval-augmented QA, citation traceability, and exam-oriented workflows.

---

## 1. Scope

- **Dataset description**: Defines the composition of learner- or institution-owned corpora, sourcing assumptions, format constraints, and privacy/ethics notes (aligned with common dataset documentation cards, adapted to private corpora).
- **Evaluation plan**: Executable dimensions, operational guidance, milestones, and deliverables for reviewers.

The in-app **Dataset & Evaluation** page renders this file. Each **subject (knowledge base)** can store an independent **dataset description** field for reporting (editable under the subject’s Documents page or on the Dataset & Evaluation screen).

Authoritative copy in-repo: `docs/DATASET_AND_EVALUATION.md`.

---

## 2. Dataset description

### 2.1 Data categories (within StudyForge)

| Category | Typical content | Lifecycle notes |
|----------|-----------------|-----------------|
| **Subject** | Logical KB unit (name, optional general description, **dataset description**) | Deleting a subject removes linked conversations and stored documents per server policy |
| **Source documents** | PDF / PPTX slides, readings | Parsed and indexed into vectors (and graph pipelines where enabled) |
| **Conversations** | Questions, answers, optional tool traces | Bound to subject + conversation IDs for audits and regression samples |
| **Exam materials** | Exam PDFs and structured items after parsing | Often privacy-sensitive; restrict environments accordingly |
| **Derived artifacts** | Mind maps, graph exports, analysis reports | Depend on upstream docs and model/version snapshots |

Excluded without authorization: bulk crawls of third-party sites, identifiable personal data (unless cleared and de-identified).

### 2.2 Sources & assumptions

- **Provenance**: Assume uploads are **explicitly permitted** for teaching or personal study.
- **Representativeness**: Coverage differs by chapter, edition, and language mix—document subject lists, approximate page/slide counts, and primary language.
- **Time span**: Record collection or syllabus revision dates to justify knowledge-cutoff statements.

### 2.3 Format & quality

- **PDF**: Scanned vs text-native materially affects OCR/parsing; note scan ratio or spot-check outcomes.
- **PPTX**: Animations, speaker notes, hidden slides may skew extraction—state whether notes are relied upon.
- **Multilingual**: Estimate language shares to interpret retrieval variance.

### 2.4 Recommended metadata (minimum)

Maintain alongside experiments:

- Subject ID / display name  
- Document inventory: filename, pages/slides, optional checksum, upload timestamp  
- **Index snapshot**: embedding provider/model (if recorded externally), graph mode on/off  
- **LLM snapshot (no secrets)**: binding, model id, host  

Per-subject **dataset descriptions** in StudyForge should summarize this in prose for examiners.

### 2.5 Privacy, compliance & retention

- Exam scripts may contain **PII**—keep deployments closed; redact or synthesize public demos.
- Align retention with institutional policy; subject deletion should trigger coordinated cleanup of uploads and indices per deployment.
- Logs may include request IDs—never paste live API keys into reports.

---

## 3. Evaluation goals & principles

| Principle | Meaning |
|-----------|---------|
| **Task fit** | Metrics reflect tutoring/exam-analysis tasks, not generic LM perplexity alone |
| **Traceability** | Measure groundedness and whether citations map to correct pages/blocks |
| **Reproducibility** | Freeze model IDs, index snapshots, and query-set construction rules |
| **Cost awareness** | Track latency, tokens, and embedding calls |

---

## 4. Evaluation plan

### 4.1 Phases (recommended)

1. **Baseline**: 1–2 subjects, fixed corpus + model config; validate ingest → index → answer path.  
2. **Small human eval**: 20–50 queries spanning frequent student questions; dual annotators score groundedness & usefulness.  
3. **Regression**: After retrieval/model changes, rerun the same query set and compare.  
4. **Deep dives (optional)**: Parsing accuracy, graph coherence, tool-heavy workflows.

### 4.2 RAG & QA quality

- **Faithfulness**: Claims supported by retrieved evidence vs hallucinated detail.  
- **Relevance**: Addresses prompt intent, including multi-part questions.  
- **Completeness**: Rubric-based scoring for structured answers.

Use Likert 1–5 or pass/fail; archive retrieval snippets per query.

### 4.3 Citations & provenance

- Sample whether citations resolve to real pages/blocks.  
- Track **high-confidence answers lacking citations** as a risk KPI.

### 4.4 Graph & extraction (if enabled)

- Spot-check entities/relations against source text.  
- Watch for over-merged entities or fragmented nodes harming QA.

### 4.5 Exam workflows

- Field-level accuracy vs human annotation (IDs, stems, options).  
- Downstream tasks (e.g., explanations, rubric grading) need domain rubrics.

### 4.6 Systems & operations

- **P95 latency** (time-to-first-token vs full completion—pick one and stick to it).  
- Error budgets: HTTP 5xx, timeouts, empty retrieval rates.  
- **Economics**: Tokens per session, embedding batches.

### 4.7 Milestone template

| Milestone | Timing (example) | Deliverable |
|-----------|------------------|-------------|
| M1 Corpus freeze | Week 1 | Subject doc manifest + hashes/page counts |
| M2 Query set & rubric | Week 2 | Query sheet + annotation guide |
| M3 Baseline eval | Week 3 | Score sheet + exemplar failures |
| M4 Delta report | Week 4 | Before/after table + limitations |

---

## 5. Relation to bundled LightRAG benchmarks

The vendored **LightRAG** tree documents public benchmarks and batch scripts (`LightRAG/README-zh.md`, etc.). If you compare against them:

- Add a short subsection naming the benchmark, split policy, and script entrypoint.  
- Keep **StudyForge operational corpora** separate from **public benchmark runs** in write-ups to avoid dataset confusion.

---

## 6. Revision history

| Version | Date | Notes |
|---------|------|-------|
| 1.1 | May 2026 | English baseline + per-subject dataset description feature |
| 1.0 | May 2026 | Initial Chinese template |
