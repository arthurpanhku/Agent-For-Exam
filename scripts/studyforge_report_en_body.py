# ruff: noqa: E501
"""Long-form English narrative blocks for `build_studyforge_final_report_en.py`.

Separated for readability; paragraphs are fed to `body()` one at a time.
"""

from __future__ import annotations

from typing import Any, Callable


def add_long_form_sections(
    doc: Any,
    *,
    h: Callable[[Any, int, str], None],
    body: Callable[[Any, str], None],
    bullet_list: Callable[[Any, list[str]], None],
    after_section3_heading: Callable[[Any], None] | None = None,
) -> None:
    """Populate the main technical narrative (mirrors the reference report's depth).

    If ``after_section3_heading`` is provided, it runs immediately after the Section 3 heading
    (e.g., to insert Figure 1 before subsection 3.1 text references it).
    """

    h(doc, 1, "Abstract")
    for p in ABSTRACT:
        body(doc, p)

    h(doc, 1, "1. Background and Significance")
    h(doc, 2, "1.1 Motivation: friction in course-scale knowledge work")
    for p in S1_1:
        body(doc, p)
    bullet_list(doc, S1_1_BULLETS)

    h(doc, 2, "1.2 Why graph-augmented RAG matters for learning")
    for p in S1_2:
        body(doc, p)
    bullet_list(doc, S1_2_BULLETS)

    h(doc, 2, "1.3 Flat retrieval, hand-built ontologies, and the pragmatic design point")
    for p in S1_3:
        body(doc, p)

    h(doc, 1, "2. Approach and Application Scenario")
    h(doc, 2, "2.1 Overall technical solution")
    for p in S2_1:
        body(doc, p)
    bullet_list(doc, S2_1_BULLETS)

    h(doc, 2, "2.2 Document processing and representation learning")
    for p in S2_2:
        body(doc, p)
    bullet_list(doc, S2_2_BULLETS)

    h(doc, 2, "2.3 Hybrid retrieval and answer synthesis")
    for p in S2_3:
        body(doc, p)
    bullet_list(doc, S2_3_BULLETS)

    h(doc, 2, "2.4 Agentic orchestration without monolithic prompts")
    for p in S2_4:
        body(doc, p)
    bullet_list(doc, S2_4_BULLETS)

    h(doc, 2, "2.5 Representative end-to-end workflow")
    for p in S2_5:
        body(doc, p)
    bullet_list(doc, S2_5_BULLETS)

    h(doc, 2, "2.6 Testable hypotheses carried by the architecture")
    for p in S2_6:
        body(doc, p)
    bullet_list(doc, S2_6_BULLETS)

    h(doc, 2, "2.7 Collaboration affordances for instructional teams")
    for p in S2_7:
        body(doc, p)
    bullet_list(doc, S2_7_BULLETS)

    h(doc, 1, "3. Detailed System Implementation")
    if after_section3_heading is not None:
        after_section3_heading(doc)
    h(doc, 2, "3.1 Layered architecture and technology stack")
    for p in S3_1:
        body(doc, p)
    bullet_list(doc, S3_1_BULLETS)

    h(doc, 2, "3.2 Document ingestion, parsing, and chunking policy")
    for p in S3_2:
        body(doc, p)
    bullet_list(doc, S3_2_BULLETS)

    h(doc, 2, "3.3 Knowledge-graph extraction, fusion, and visualization")
    for p in S3_3:
        body(doc, p)
    bullet_list(doc, S3_3_BULLETS)

    h(doc, 2, "3.4 Query interfaces: modes, streaming, and grounding discipline")
    for p in S3_4:
        body(doc, p)
    bullet_list(doc, S3_4_BULLETS)

    h(doc, 2, "3.5 Conversational agent: tools, citations, and pedagogical modes")
    for p in S3_5:
        body(doc, p)
    bullet_list(doc, S3_5_BULLETS)

    h(doc, 2, "3.6 Exam-oriented intelligence: parsing, analysis pipelines, and variants")
    for p in S3_6:
        body(doc, p)
    bullet_list(doc, S3_6_BULLETS)

    h(doc, 2, "3.7 Integration, deployment, and engineering hygiene")
    for p in S3_7:
        body(doc, p)
    bullet_list(doc, S3_7_BULLETS)

    h(doc, 2, "3.8 Streaming event models and robustness under provider variance")
    for p in S3_8:
        body(doc, p)
    bullet_list(doc, S3_8_BULLETS)

    h(doc, 2, "3.9 Academic integrity, oversight, and constructive use of generative affordances")
    for p in S3_9:
        body(doc, p)
    bullet_list(doc, S3_9_BULLETS)

    h(doc, 2, "3.10 Limitations, open problems, and roadmap")
    for p in S3_10:
        body(doc, p)
    bullet_list(doc, S3_10_BULLETS)

    h(doc, 1, "4. Evaluation Strategy, Failure Modes, and Responsible Deployment")
    h(doc, 2, "4.1 What validation means when the corpus is user-owned")
    for p in S4_1:
        body(doc, p)

    h(doc, 2, "4.2 Observability, regression containment, and operational guardrails")
    for p in S4_2:
        body(doc, p)
    bullet_list(doc, S4_2_BULLETS)

    h(doc, 2, "4.3 Demonstrations without production credentials")
    for p in S4_3:
        body(doc, p)

    h(doc, 2, "4.4 Reproducibility checklist for independent auditors and peer reviewers")
    for p in S4_4:
        body(doc, p)
    bullet_list(doc, S4_4_BULLETS)

    h(doc, 1, "5. Complete Product Feature Inventory")
    for p in S5_FEATURE_INTRO:
        body(doc, p)

    h(doc, 2, "5.1 Knowledge bases, metadata, and dataset documentation")
    bullet_list(doc, S5_F1_BULLETS)
    h(doc, 2, "5.2 Document ingestion and indexing")
    bullet_list(doc, S5_F2_BULLETS)
    h(doc, 2, "5.3 Hybrid retrieval, graph exploration, and citations")
    bullet_list(doc, S5_F3_BULLETS)
    h(doc, 2, "5.4 Conversations, streaming chat, and tool orchestration")
    bullet_list(doc, S5_F4_BULLETS)
    h(doc, 2, "5.5 Exams: upload, parsing, re-parse, and analysis workflows")
    bullet_list(doc, S5_F5_BULLETS)
    h(doc, 2, "5.6 Mind maps and visualization exports")
    bullet_list(doc, S5_F6_BULLETS)
    h(doc, 2, "5.7 Settings: multi-scene LLM, embeddings, OCR hosts, and encrypted keys")
    bullet_list(doc, S5_F7_BULLETS)
    h(doc, 2, "5.8 Security, observability, and API ergonomics")
    bullet_list(doc, S5_F8_BULLETS)
    h(doc, 2, "5.9 Packaging: Docker stacks, launcher scripts, and contract tests")
    bullet_list(doc, S5_F9_BULLETS)

    h(doc, 1, "6. Summary")
    h(doc, 2, "6.1 Technical strengths")
    bullet_list(doc, S5_1_BULLETS)
    h(doc, 2, "6.2 Contributions")
    for p in S5_2:
        body(doc, p)

    h(doc, 2, "6.3 Deployment envelopes—from single-course pilots to departmental scale")
    for p in S5_3:
        body(doc, p)
    bullet_list(doc, S5_3_BULLETS)


S5_FEATURE_INTRO = [
    (
        "Beyond architectural narrative, stakeholders often require an explicit checklist of product-facing "
        "capabilities. The following inventory mirrors the StudyForge repository as an integrated application—not "
        "only algorithms—spanning ingestion, retrieval modes, conversational agents, exam tooling, operational "
        "policies, and documentation surfaces intended for reproducibility and committee review."
    ),
]

S5_F1_BULLETS = [
    "Subjects (knowledge bases) with create/list/get/update/delete lifecycle backed by durable metadata.",
    "Optional general descriptions plus a dedicated per-subject dataset_description field for corpora and evaluation notes.",
    "Sidebar navigation coupling subjects with conversations, including exam-analysis threads.",
]

S5_F2_BULLETS = [
    "Courseware uploads for PDF and PPTX with server-side limits and asynchronous indexing status tracking.",
    "Per-subject document listings with detail inspection hooks and deletion semantics tied to storage cleanup policies.",
    "Integration paths into embedding-backed chunk stores and optional graph construction pipelines.",
]

S5_F3_BULLETS = [
    "Multiple retrieval/query modes (including naive/local/global/mix-style exposures through the API) for experimentation.",
    "Interactive knowledge-graph visualization and drill-down experiences grounded in extracted entities and relations.",
    "Answer synthesis pathways designed to surface citations tied to pages or slide identities when indexing completes.",
]

S5_F4_BULLETS = [
    "Conversation-centric UX with streaming responses suitable for long-form tutoring exchanges.",
    "Tool-using agent pathways registering backend capabilities such as document listing, graph querying, paged reads, and mind-map synthesis.",
    "Subject-scoped threads preserving provenance for auditing and regression comparisons.",
]

S5_F5_BULLETS = [
    "Exam PDF ingestion with processing lifecycles (pending/processing/completed/failed) surfaced in the UI.",
    "Structured question browsing, metadata edits (e.g., exam year), re-parse triggers, and destructive cleanup where permitted.",
    "Exam-analysis conversations that batch-select completed papers to spawn dedicated analytic chat workflows.",
]

S5_F6_BULLETS = [
    "Mind-map generation experiences leveraging the same conversational substrate and export-friendly representations.",
]

S5_F7_BULLETS = [
    "Settings UI with separate bindings for knowledge-graph extraction, chat, mind-map models, embeddings, and OCR providers.",
    "OpenAI-compatible gateways (commonly used with DeepSeek-class hosts) alongside SiliconFlow-style catalogs where configured.",
    "Server-side encryption-at-rest for provider keys plus unified provider keys where the deployment enables them.",
]

S5_F8_BULLETS = [
    "Optional HTTP gateway API keys with OpenAPI-visible schemes for disciplined external integrations.",
    "Request correlation IDs echoed through JSON error bodies and headers for traceability.",
    "Health endpoints suitable for orchestrators and smoke automation.",
]

S5_F9_BULLETS = [
    "Docker Compose stacks for production-style and live-reload developer deployments.",
    "Cross-platform starter/stop scripts mirroring native uvicorn + Vite workflows.",
    "pytest contract coverage for critical middleware behaviors and automated English report generation scripts.",
    "In-app Dataset & Evaluation documentation rendered from version-controlled Markdown for reviewers.",
]


ABSTRACT = [
    (
        "StudyForge is an intelligent learning workspace designed around a simple scientific claim: when instructional "
        "materials are available as learner-owned corpora, the most useful assistant is not a monolithic chat model, "
        "but a retrieval stack that exposes provenance, structural relationships, and controlled generation. "
        "Concretely, the platform couples asynchronous document ingestion for PDF and PPTX, embedding-backed chunk "
        "indices, and LightRAG-style graph construction so that queries can be answered with explicit ties to source "
        "locations (pages or slides). On top of this substrate, StudyForge layers streaming conversational interfaces, "
        "optional tool-using agents, and exam-centric workflows that reuse the same retrieval primitives rather than "
        "forking ad hoc pipelines."
    ),
    (
        "From a systems perspective, the architectural bet is modularity: FastAPI acts as an orchestration gateway with "
        "typed routes and predictable payload schemas; the browser client focuses on interaction latency and information "
        "layout; and model providers remain interchangeable behind OpenAI-compatible bindings for chat, extraction, "
        "and embeddings. This separation matters because educational deployments routinely change suppliers (cost, "
        "latency, compliance), and because embeddings are often the limiting factor for throughput during indexing. "
        "StudyForge therefore treats credential management as a first-class concern—configuration surfaces distinguish "
        "extraction for graph construction from chat models used for answering, and vector backends can be pointed at "
        "hosted APIs or local runtimes when permitted."
    ),
    (
        "This report follows the narrative structure of a full project technical memorandum: we motivate the problem "
        "in pedagogical and knowledge-management terms, articulate the conceptual approach (graph-augmented retrieval, "
        "multi-mode querying, agentic orchestration), and then drill into implementation choices at the level an "
        "engineering lead would expect—chunking policy, graph lifecycle, streaming protocols, and exam analysis "
        "pipelines. We close with an evaluation philosophy aligned with real deployments: correctness is conditional "
        "on corpus coverage, latency interacts with model budgets, and transparent failure modes beat opaque retries."
    ),
    (
        "Methodologically, we treat the assistant as an empirical instrument whose behavior is jointly determined by "
        "corpus segmentation, embedding geometry, graph extraction prompts, and decoding policies. Small shifts—"
        "overlap width, temperature, extraction batching—can produce disproportionate changes in downstream citing "
        "patterns; reporting therefore emphasizes reproducible configuration snapshots rather than single headline "
        "accuracy numbers divorced from setup."
    ),
    (
        "The engineering narrative foregrounds interfaces between humans and automation: instructors curate what enters "
        "the knowledge base; learners interpret citations rather than trusting fluent prose; developers inspect traces "
        "when orchestrated pipelines stall. Such role clarity avoids the category error of treating LLMs as infallible "
        "oracles and aligns with responsible deployment guidance emerging across universities."
    ),
    (
        "Finally, we articulate limits honestly. Graph-augmented RAG reduces certain failure modes but introduces others—"
        "noisy triples, over-merged entities, spurious relational shortcuts—and variant generation can facilitate "
        "practice or shortcuts depending on governance. The concluding sections summarize strengths while naming "
        "mitigations (human review, schema validation, configurable modes) that keep automation subsidiary to pedagogy."
    ),
]


S1_1 = [
    (
        "University courses rarely ship knowledge as a tidy database. Instead, instructors distribute dense slide decks "
        "and readings whose semantics are spread across titles, bullet hierarchies, speaker notes, figures, and "
        "occasionally scanned fragments. Learners face four recurring costs: extracting durable concepts from ephemeral "
        "layouts; reconstructing prerequisite structure that is implicit in exposition; locating precise references "
        "when studying for exams; and generating practice that reflects the course’s style without outsourcing "
        "understanding to unconstrained generation."
    ),
    (
        "Traditional keyword search reduces the third cost only partially, because lexical overlap does not guarantee "
        "conceptual proximity, and because slide decks reuse vocabulary across unrelated topics. Pure large-language-model "
        "chat reduces friction but introduces a subtler risk: fluent answers can omit boundaries, confuse similar "
        "definitions, or silently extrapolate beyond the provided documents. A practical assistant must therefore "
        "optimize not only helpfulness but epistemic hygiene—what evidence was used, where it lives in the materials, "
        "and whether multiple passages disagree."
    ),
]


S1_1_BULLETS = [
    "Extraction overhead: manual summarization and flashcard authoring scale poorly across semesters and teaching staff churn.",
    "Structural blindness: linear PDF viewers hide prerequisite chains, contrasts, and recurring motifs across lectures.",
    "Retrieval latency and precision: students need answers anchored to page/slide identities, not generic textbook prose.",
    "Assessment logistics: authentic practice items should mirror local norms (terminology, difficulty, format) while remaining varied.",
]


S1_2 = [
    (
        "LightRAG-style pipelines occupy a productive middle ground between unstructured retrieval and curated "
        "knowledge engineering. By extracting entities and relationships from chunked text with LLM supervision, the "
        "system materializes a lightweight graph that supports global reasoning cues without demanding months of manual "
        "ontology design. When fused with dense retrieval over the same chunks, the graph acts as a corrective signal: "
        "it privileges coherent neighborhoods of concepts and discourages answers stitched from superficially similar "
        "but semantically distant passages."
    ),
    (
        "For StudyForge, graph construction is not ornamental. It drives secondary experiences—interactive visualization, "
        "entity-centric drill-down, and richer prompts for downstream agents—while remaining accountable to source "
        "metadata. The pedagogical hypothesis is that making relationships visible improves comprehension and transfers "
        "to exam performance when learners connect declarative facts with the explanatory edges between them."
    ),
]


S1_2_BULLETS = [
    "Operational efficiency: automated indexing amortizes instructor effort once ingestion pipelines are dependable.",
    "Interpretability: explicit entities and relations scaffold explanation and debugging when answers look wrong.",
    "Technical generality: OpenAI-compatible gateways allow swapping chat and embedding models as budgets evolve.",
    "Research-facing value: the stack is a reproducible sandbox for comparing retrieval modes under identical corpora.",
]


S1_3 = [
    (
        "Pure vector RAG without relational structure often excels at lexical proximity yet struggles when answers "
        "require traversing multi-hop arguments implicit across slides—definitions introduced early, examples revisiting "
        "them weeks later, contrasts buried in tables. Conversely, hand-authored knowledge graphs deliver precision "
        "but impose taxonomy maintenance burdens incompatible with fast-moving courses. LightRAG-centric pipelines aim "
        "for amortized structure: pay extraction costs once per corpus refresh, then exploit relational summaries "
        "whenever learners query or visualize."
    ),
    (
        "The pragmatic design point is not maximal automation but controlled delegation: machines propose entities and "
        "edges; interfaces expose provenance so humans can disagree constructively with the model without forking the "
        "entire stack. StudyForge encodes that philosophy through dual surfaces—numeric retrieval modes plus visual "
        "graph exploration—so skepticism has somewhere actionable to land."
    ),
    (
        "Positioned against enterprise LMS search boxes and generic chat overlays, the approach is intentionally "
        "research-software adjacent: opinionated about retrieval transparency, permissive about provider selection, and "
        "extensible where pedagogy demands bespoke prompts or localized evaluation harnesses."
    ),
]


S2_1 = [
    (
        "StudyForge implements a retrieval-augmented assistant whose retrieval substrate combines vector similarity with "
        "graph-derived structure. The backend ingests PDF and PPTX artifacts, normalizes text, attaches provenance "
        "metadata, embeds chunks, and schedules LightRAG indexing tasks that populate entity and relationship stores "
        "alongside chunk vectors. Queries traverse multiple retrieval pathways—local, global, naive, and mixed modes—"
        "reflecting different granularities of evidence aggregation before an LLM composes a final response."
    ),
    (
        "A parallel agentic layer handles tasks that benefit from decomposition: conversational agents register tools "
        "that call back into retrieval services; exam analysis pipelines batch questions under a lead orchestrator "
        "that emits traces suitable for streaming user interfaces. This mirrors modern LLM application design—thin "
        "orchestration, heavy reuse of shared primitives, strict schemas at boundaries—while avoiding a single "
        "megaprompt that must implicitly encode every policy."
    ),
]


S2_1_BULLETS = [
    "Core stack: FastAPI services, Vue 3 single-page client, LightRAG integration, OpenAI-compatible LLM bindings.",
    "Front-end affordances: subject workspaces, chat panels, graph visualization, exam tooling surfaces.",
    "Delivery: Docker-oriented workflows and developer scripts that pair API processes with Vite for rapid iteration.",
]


S2_2 = [
    (
        "Document preprocessing is where retrieval quality is truly decided. Slides encode semantics through layout; "
        "PDFs encode them through typographic hierarchy and page breaks. StudyForge therefore preserves slide/page "
        "indices as first-class metadata so chunk boundaries respect natural segmentation where possible, splitting "
        "only when length constraints demand it. Normalization removes repetitive headers and brittle OCR artifacts "
        "when present, reducing noise that otherwise pollutes embeddings and misleads extraction prompts."
    ),
    (
        "Embeddings turn unstructured chunks into searchable vectors; LLM extraction turns those same chunks into "
        "candidate entities and relations. The combination matters because vectors excel at recall while graphs excel "
        "at constraining composition: answers should cite chunks, while extracted concepts summarize recurrent motifs "
        "across chunks. Asynchronous scheduling ensures uploads return quickly while long-running indexing proceeds "
        "with explicit status endpoints suitable for polling user interfaces."
    ),
    (
        "Noise sensitivity deserves explicit discussion: duplicated institutional logos, recurring slide footers, and OCR "
        "speckle can dominate token budgets unless normalization strips them early. Conversely, aggressive cleaning "
        "risks deleting equations or marginal annotations that carry exam-critical detail. StudyForge biases toward "
        "conservative retention of mathematical tokens while collapsing predictable boilerplate—tunable heuristics "
        "teams can adapt per discipline."
    ),
]


S2_2_BULLETS = [
    "PPTX parsing extracts titles, bullets, and notes; PDF parsing preserves page-bound contexts for citations.",
    "Chunk metadata carries file identifiers and positional indices for downstream UI highlighting.",
    "Batch-friendly embedding calls amortize provider overhead during large deck ingestion.",
]


S2_3 = [
    (
        "Hybrid retrieval can be understood as a controlled fusion problem: merge candidate passages from chunk-level "
        "vector search with signals induced by entity-relationship neighborhoods and higher-level graph abstractions. "
        "LightRAG exposes query modes that emphasize different balances—local responses prioritize tightly coupled "
        "context; global responses lean on broader summaries encoded in graph machinery; mix modes seek robustness for "
        "general student questions where neither extreme dominates."
    ),
    (
        "Downstream answer synthesis must remain disciplined. Streaming NDJSON responses allow the UI to render partial "
        "progress while preserving structured fields for citations and optional analytic addenda (for example, "
        "summaries of evidentiary tension across passages). The architectural implication is that prompts and parsers "
        "co-evolve: retrieval provides candidates, but the contract between middleware and UI dictates what “grounded” "
        "means operationally."
    ),
]


S2_3_BULLETS = [
    "Multi-path retrieval improves recall while graph signals temper incoherent stitching.",
    "Configurable modes let instructors emphasize precision (local) versus syllabus-wide synthesis (global).",
    "Streaming improves perceived latency on long generations without sacrificing structured annotations.",
]


S2_4 = [
    (
        "Agents are valuable when they encapsulate policies that would clutter application code: multi-step reasoning, "
        "conditional tool calls, and narrative scaffolding such as Socratic dialogue. StudyForge’s conversational agent "
        "path registers capabilities that map cleanly onto retrieval services rather than bespoke microservices. Tool "
        "calls therefore remain audit-able—they expose function names, arguments, and outcomes—while the LLM focuses "
        "on language-level planning constrained by retrieved evidence."
    ),
    (
        "Exam analysis adopts a complementary pattern: a lead orchestrator fans out batched work to sub-agents that "
        "process contiguous question groups, emitting traces and events consumed by the front end. This structure "
        "supports long-running analyses without blocking the interactive chat loop, and it mirrors how human teaching "
        "assistants parallelize grading preparation—partition the workload, maintain consistent rubric context, merge "
        "results."
    ),
]


S2_4_BULLETS = [
    "Modular agents reduce coupling between chat UX and heavy analytical workflows.",
    "Batch concurrency trades throughput against provider rate limits with explicit semaphores.",
    "Trace emission enables transparency when intermediate reasoning must be inspected or demonstrated.",
]


S2_5 = [
    (
        "A typical deployment session begins with library creation: users organize materials into subjects that scope "
        "conversations and retrieval indices. Uploading PDF or PPTX artifacts triggers asynchronous parsing and "
        "embedding, followed by graph extraction when credentials permit. The UI surfaces completion states so users "
        "understand when hybrid queries will reflect fresh content versus stale indices."
    ),
    (
        "Once indexing completes, learners interact through chat with explicit retrieval mode selection, inspect "
        "relationship diagrams when curiosity drives structural understanding, and optionally invoke exam-centric flows "
        "that consume parsed papers and generated variants. Instructors may emphasize citation fidelity during review "
        "season or exploratory browsing during initial comprehension—StudyForge provides knobs rather than a single "
        "behavioral preset."
    ),
]


S2_5_BULLETS = [
    "Upload → index → visualize → query → (optional) analyze exams → iterate with new materials.",
    "Subject boundaries prevent cross-course leakage and simplify operational resets.",
    "Status endpoints support resilient UX patterns under variable provider latency.",
]


S2_6 = [
    (
        "Architectures encode hypotheses even when teams skip formal experiments. Here, the central hypothesis is "
        "that exposing relational scaffolding measurably improves the stability of grounded answers compared with "
        "identical decoding budgets under naive chunk retrieval alone—especially for questions that hinge on "
        "contrasts, prerequisites, or terminology disambiguation repeated across lectures."
    ),
    (
        "A second hypothesis concerns throughput fairness: batched embedding plus asynchronous graph extraction "
        "should keep interactive chat responsive while indexing proceeds, avoiding the disappointing pattern where "
        "demos stall on projector Wi-Fi because monolithic pipelines block the event loop."
    ),
    (
        "Third, variant-generation workflows should preserve statistical diversity—multiple items probing the same "
        "competency—without trivial surface paraphrase that yields duplicate reasoning paths. Evaluating that claim "
        "requires rubrics beyond BLEU scores: instructor judgment, Bloom tagging, and adversarial checks for leaked "
        "answers from memorization surfaces."
    ),
    (
        "Finally, transparency hypotheses matter pedagogically: learners who can inspect citations and graph neighbors "
        "calibrate trust better than learners exposed only to fluent monologues. While causal claims demand user "
        "studies beyond this engineering report, the interface is intentionally instrumented to support such studies."
    ),
]


S2_6_BULLETS = [
    "Hypothesis A: graph cues reduce incoherent multi-chunk fusion versus pure top-k baselines at matched latency.",
    "Hypothesis B: asynchronous orchestration preserves UX interactivity during expensive indexing phases.",
    "Hypothesis C: structured variant prompts diversify cognitive coverage when validated by instructors.",
    "Hypothesis D: provenance-rich UI affordances improve appropriate trust—not blind reliance—on model outputs.",
    "These hypotheses map cleanly onto A/B fixtures in classroom pilots without rewriting core services.",
]


S2_7 = [
    (
        "Instruction is seldom solitary: teaching assistants revise slides, faculty swap modules mid-semester, and "
        "students contribute clarifying notes. StudyForge encodes collaboration implicitly through subject-scoped "
        "libraries—upload privileges, shared visualization sessions, and reproducible traces that newcomers can replay "
        "to understand how an analysis conclusion emerged."
    ),
    (
        "Version discipline matters when slides mutate weekly. While full Git-like semantics for instructional PDFs "
        "remain future work, anchoring citations to file identifiers plus page offsets yields minimally viable provenance "
        "when decks rev. Teams should nonetheless adopt naming conventions that signal revision epochs externally."
    ),
    (
        "From an organizational standpoint, transparent orchestration lowers onboarding costs: a new TA can watch "
        "streaming traces during exam alignment reviews rather than reverse-engineering opaque scripts. That sociotechnical "
        "benefit parallels the technical payoff of modular services."
    ),
    (
        "Finally, cross-role empathy improves design: engineers learn pacing constraints of live seminars; instructors "
        "learn latency envelopes of remote embeddings. Joint pilots therefore outperform isolated hackathons—StudyForge "
        "targets that reality with logs instructors can read without SSH access."
    ),
]


S2_7_BULLETS = [
    "Subject boundaries approximate tenant boundaries for classroom-sized deployments.",
    "Encourage documented upload policies so corpora remain internally consistent.",
    "Use traces as synchronous teaching artifacts during TA training sessions.",
    "Pair automation with office-hour workflows where humans adjudicate borderline extractions.",
    "Capture qualitative feedback loops—not only quantitative retrieval scores.",
    "Treat UX copy as part of the safety surface (defaults, warnings, recovery paths).",
]


S3_1 = [
    (
        "Figure 1 summarizes the deployment layering: browser client, API gateway, retrieval core, and configurable "
        "models. The front end communicates through REST and streaming endpoints; the gateway authenticates requests "
        "when configured, attaches correlation identifiers, and delegates domain logic to services that understand "
        "subjects, conversations, documents, graphs, and exams. Storage layouts separate uploaded binaries, derived "
        "text artifacts, indices, and analytic traces so backups and deletion policies can be reasoned about clearly."
    ),
    (
        "The model layer is deliberately polymorphic. Chat models power fluent answers and agent planning; extraction "
        "models populate graphs; embedding models determine semantic neighborhoods. StudyForge encodes these roles in "
        "configuration so teams can adopt DeepSeek-class endpoints for reasoning while sourcing embeddings from "
        "another vendor—or from local GPU inference—without rewriting retrieval mathematics."
    ),
]


S3_1_BULLETS = [
    "FastAPI provides OpenAPI schemas that contract-test critical surfaces for regressions.",
    "Vue 3 + Vite emphasize modular panels (documents, chat, graph, exam tooling) with shared state conventions.",
    "Middleware hooks (API keys, request IDs) align with classroom pilots that require lightweight access control.",
]


S3_2 = [
    (
        "Chunking is treated as a retrieval hyperparameter. Too-small fragments lose definitional context; too-large "
        "blocks dilute embeddings and encourage vague answers. Slide-aware segmentation exploits presentation "
        "structure: bullets co-occur because instructors intended them together. When decks overflow token budgets, "
        "deterministic splitting retains overlapping windows so continuity survives mechanical cuts."
    ),
    (
        "Operational throughput hinges on embedding batching and parallel inserts. Classroom demonstrations fail when "
        "indexing stalls silently; StudyForge therefore emphasizes observable stages—parse, embed, extract—surfaced "
        "through API status fields the UI can interpret. This observability doubles as pedagogy for student developers "
        "learning how modern RAG systems behave under load."
    ),
]


S3_2_BULLETS = [
    "Metadata-rich chunks unlock citation UI and graph node provenance.",
        "Parallel pipelines reduce wall-clock time for mid-sized corpora typical of single-course deployments.",
        "Explicit failures (missing keys, embedding errors) are preferable to partially constructed graphs.",
]


S3_3 = [
    (
        "Graph extraction prompts bias the model toward concise, schema-aligned entities and relations—shorthand for "
        "concepts the course revisits, not encyclopedic nodes unrelated to local objectives. LightRAG merges vectorized "
        "representations of entities and relationships with structural stores so retrieval can hop between lexical and "
        "topological similarity measures depending on mode."
    ),
    (
        "Visualization translates abstract triples into manipulable diagrams: node palettes communicate entity classes; "
        "hover states expose snippets and sources; filters tame dense graphs produced from ambitious syllabi. The goal "
        "is not cinematic graphics but cognitive scaffolding—learners should perceive clusters, hubs, and bridging "
        "concepts that textual reading obscures."
    ),
    (
        "Layout physics implicitly communicates importance: high-degree nodes migrate toward visual centrality under "
        "force-directed solvers, signaling conceptual hubs instructors may wish to reinforce orally. Filtering by "
        "entity type lets novices reduce clutter without sacrificing depth—analogous to progressive disclosure patterns "
        "in IDE tooling."
    ),
    (
        "Synchronizing graph selection with document viewers closes the loop between symbolic and textual modalities: "
        "clicking a formula entity might reveal its definitional slide; highlighting an exam topic cluster might cue "
        "related assessment blueprints. Achieving tight synchronization demands stable identifiers bridging graph nodes "
        "and chunk metadata—a contract StudyForge encodes at ingestion time."
    ),
]


S3_3_BULLETS = [
        "Extraction quality improves when headings and slide titles participate in prompts as weak supervision.",
        "Graph hygiene (deduplication, pruning noisy edges) keeps visualization interpretable.",
        "Interactive filtering aligns UI complexity with learner intent (review chapter vs explore globally).",
]


S3_4 = [
    (
        "StudyForge exposes LightRAG query modes as explicit user choices because retrieval trade-offs are pedagogically "
        "meaningful. A student verifying a definition benefits from local precision; another synthesizing exam guides "
        "may tolerate broader abstraction if citations remain inspectable. Bypass-style paths exist for diagnostic "
        "scenarios where operators must isolate model behavior from retrieval, underscoring that not every failure "
        "originates in embeddings."
    ),
    (
        "Streaming contracts deserve engineering attention. Partial tokens improve responsiveness, but structured "
        "annotations—citations, tool traces, conflict summaries—must remain machine-parseable. The implementation "
        "therefore favors disciplined event shapes over ad hoc concatenation, easing automated testing and downstream "
        "analytics that ingest session logs."
    ),
]


S3_4_BULLETS = [
        "Mode selectors make retrieval hypotheses explicit rather than hiding them inside defaults.",
        "Diagnostics distinguish LLM errors from indexing gaps during support workflows.",
        "Structured streaming enables progressive rendering without sacrificing programmatic consumers.",
]


S3_5 = [
    (
        "Tool-using agents operationalize the principle that language models should plan but not secretly substitute "
        "for retrieval. Functions expose narrowly scoped capabilities—graph queries, structured lookups—while system "
        "prompts articulate citation discipline and classroom tone. Optional stylistic augmentations (for example, "
        "Socratic prompting) reshape interaction goals without rewriting retrieval code paths."
    ),
    (
        "Citation analysis hooks acknowledge an uncomfortable truth: retrieval reduces hallucination rates but does not "
        "eliminate rhetorical overreach. Surfacing trust diagnostics (when configured) trains users to read outputs "
        "critically—an educational stance aligned with institutional integrity policies more than pure automation hype."
    ),
]


S3_5_BULLETS = [
        "Registered tools keep capabilities enumerable for audits and capability matrices.",
        "Pedagogical modes map to prompt augmentations rather than forked agent binaries.",
        "Optional analytic tails reinforce meta-cognitive habits around evidence usage.",
]


S3_6 = [
    (
        "Exam materials enter the system as PDF artifacts parsed into structured representations suitable for analytics "
        "and re-use. Parsed exams become inputs to orchestrated analyses that align questions with knowledge traces "
        "recovered from course documents—linking assessment items back to the corpus that justified their placement in "
        "the curriculum. Parallel batching balances responsiveness against LLM quotas while emitting artifacts usable "
        "for teaching demonstrations."
    ),
    (
        "Variant generation endpoints consolidate pedagogy and automation: instructors specify targets—skills, difficulty "
        "bands, formats—and the stack prompts chat models under structured constraints to emit parallel questions that "
        "share latent objectives without duplicating surface wording. This complements retrieval-heavy tutoring by "
        "supplying deliberate practice, provided operators validate samples before high-stakes use."
    ),
    (
        "Parsing historically favors deterministic structure where possible: separating stems, prompts, and directive "
        "language (“Show your work”, “Choose all that apply”) stabilizes downstream analytics. When OCR ambiguity "
        "introduces jitter, human-in-the-loop correction hooks prevent error cascades into automated rubrics."
    ),
    (
        "Orchestrated exam analysis mirrors divide-and-conquer strategies familiar from industrial ML pipelines—partition "
        "items, preserve shared context (course title, assumed prerequisites), merge intermediate representations—"
        "yet surfaces outputs as teaching narratives (thinking blocks, tool traces) palatable in classroom walkthroughs."
    ),
]


S3_6_BULLETS = [
        "Lead/sub orchestration mirrors human task partitioning for exam-intelligence workloads.",
        "Trace storage supports reproducible walkthroughs during presentations or grading calibration.",
        "Structured variants enable item banks that respect Bloom-style cognitive diversity when templated accordingly.",
]


S3_7 = [
    (
        "Production-grade assistants require boring excellence: reproducible environments, secret hygiene, and smoke "
        "tests that fail loudly when assumptions drift. StudyForge ships Docker-minded workflows and developer scripts "
        "that pair API processes with front-end tooling; configuration emphasizes `.env` conventions without embedding "
        "live credentials into repositories. Contract tests guard representative HTTP behaviors so refactors do not "
        "silently fracture classroom demos."
    ),
    (
        "Documentation and repository hygiene mirror open-source expectations—README guidance, explicit licensing on "
        "vendored subgraphs where applicable, and issue-tracker-friendly module boundaries. These choices reduce "
        "activation energy for independent verification, which matters academically: reproducibility is itself a "
        "result."
    ),
]


S3_7_BULLETS = [
        "Gateway API keys (`STUDYFORGE_API_KEY`) optional enable lightweight perimeter controls.",
        "Pytest contracts encode acceptable failure semantics for core routes.",
        "Separation of uploads, indices, and traces simplifies GDPR-minded deletion experiments.",
]


S3_8 = [
    (
        "Streaming is not merely UX polish; it is a protocol contract between model providers, middleware, and "
        "clients. Partial tokens interleave with structured events carrying citations, tool traces, or pipeline "
        "progress—formats that must survive transient network faults without corrupting parsers. StudyForge favors "
        "incremental JSON or newline-delimited payloads so browsers can recover gracefully when connections flap "
        "during long generations."
    ),
    (
        "Provider variance compounds the problem: rate limits, differing stop sequences, subtly incompatible "
        "tool-calling dialects, and latency spikes during peak teaching hours. Robust clients implement backoff, "
        "request sizing discipline, and semantic duplication guards so retries do not multiply billed tokens "
        "explosively."
    ),
    (
        "From a research standpoint, streaming traces double as experiment logs: they reveal when retrieval sets "
        "collapse to empty, when models ignore citations despite prompt constraints, or when graph modes oscillate "
        "answers unpredictably. Investing in structured telemetry therefore pays analytical dividends beyond "
        "production reliability alone."
    ),
    (
        "Finally, partial failure semantics matter educationally. When extraction succeeds but graph fusion falters, "
        "the assistant should degrade to vector-only responses with explicit badges—not hallucinate graph certainty. "
        "StudyForge’s explicit modes and configuration errors operationalize that stance."
    ),
]


S3_8_BULLETS = [
    "Prefer deterministic parsers over brittle regex on free-form model transcripts.",
    "Separate transport failures from model refusals to avoid misleading retry loops.",
    "Annotate degraded modes so learners understand when structural reasoning is unavailable.",
    "Cap concurrent LLM calls per tenant to protect shared classroom backends.",
    "Version prompts alongside retrieval indices to keep longitudinal experiments comparable.",
    "Record correlation IDs end-to-end for post-mortems after failed demos.",
]


S3_9 = [
    (
        "Generative study assistants inhabit contested terrain: they can deepen understanding through Socratic dialogue "
        "and varied practice, yet they can shortcut reflective effort when defaults emphasize speed over scrutiny. "
        "StudyForge’s design leans toward inspectability—citations, explicit retrieval modes, traceable tool calls—"
        "so instructors can articulate policies (“always verify claims against slide X”) rather than banning tools "
        "wholesale."
    ),
    (
        "Exam-generation surfaces deserve explicit governance. Items intended for high-stakes assessment require "
        "human approval pipelines; items intended for low-stakes rehearsal benefit from rapid iteration. The "
        "architecture accommodates both by treating generation as a proposal stage separated from publication "
        "unless operators configure otherwise."
    ),
    (
        "Variant prompts must resist leaking answer keys embedded in sample PDFs or instructor-only appendices. "
        "Access controls on subjects, coupled with corpus hygiene practices (redacting solutions before upload), "
        "remain institutional responsibilities—software can warn but cannot substitute policy."
    ),
    (
        "Longer term, interoperable logging standards across LMS tools could let departments audit aggregate usage "
        "patterns (time-on-graph vs chat-only) and correlate them responsibly with learning analytics—provided "
        "privacy constraints are honored."
    ),
]


S3_9_BULLETS = [
    "Default UX emphasizes provenance to reinforce verification habits.",
    "Agent traces support instructor audits without exposing raw prompts unnecessarily in multi-user settings.",
    "Separate staging vs published question banks when institutional policy demands review gates.",
    "Document retention choices should follow jurisdictional guidance on student data.",
    "Communicate limitations prominently during onboarding to novice users.",
]


S3_10 = [
    (
        "Despite architectural ambition, StudyForge inherits foundational-model limitations: extraction hallucinates "
        "spurious relations; embeddings conflate distinct symbols sharing notation; long-context models may still "
        "under-weight middle passages. Mitigations include iterative prompting, graph pruning heuristics, and hybrid "
        "active learning where instructors pin authoritative nodes."
    ),
    (
        "Multimodal course materials—hand-drawn diagrams, audio overlays, video walkthroughs—remain unevenly supported "
        "when pipelines prioritize text-first extraction. Future iterations may integrate vision-language encoders "
        "with caution about compute budgets and licensing."
    ),
    (
        "Evaluation likewise remains open: automated grading rubrics for rich STEM proofs require symbolic checkers "
        "beyond generic LLM judging; personalized recommendations need longitudinal datasets most pilots lack. "
        "StudyForge positions itself as infrastructure those advances can plug into rather than the final word."
    ),
    (
        "Roadmap items include tighter regression suites conditioned on frozen corpora snapshots, finer-grained "
        "tenant isolation for departmental deployments, and teacher dashboards summarizing graph health metrics "
        "(density, orphan nodes, contradiction clusters) for continuous content improvement."
    ),
]


S3_10_BULLETS = [
    "Treat extracted graphs as hypotheses subject to curriculum review.",
    "Invest in reproducible corpus snapshots for scientific comparisons across model generations.",
    "Explore selective vision pipelines without exploding embedding costs.",
    "Couple analytics with intervention UX—not passive dashboards alone.",
    "Maintain backward-compatible APIs so downstream classroom integrations survive upgrades.",
    "Co-design governance workflows with instructional designers, not solely engineers.",
]


S4_1 = [
    (
        "Evaluation in learner-owned corpora differs from benchmark leaderboards. Ground truth is partial: slides omit "
        "steps assumed in lecture, exams test synthesis beyond literal retrieval, and student questions blend factual "
        "and strategic intents. StudyForge therefore emphasizes layered validation: mechanical checks for ingestion and "
        "index completeness; qualitative review of citations against known PDF locations; and comparative probes "
        "across retrieval modes to detect regressions when models or chunk policies change."
    ),
    (
        "Quantitative metrics remain useful when scoped honestly. Precision-recall estimates against labeled span sets, "
        "latency distributions stratified by corpus size, and human preference studies on explanation usefulness each "
        "illuminate different facets. The scientific stance is pragmatic—optimize for transparent failure and rapid "
        "iteration rather than claiming omniscient correctness from automation alone."
    ),
    (
        "A complementary strand is stress testing under adversarial or sloppy inputs: malformed uploads, near-duplicate "
        "files, contradictory edits across document versions, and questions that request prohibited assistance. Systems "
        "that behave well on curated benchmarks but collapse on messy classroom corpora fail the deployment sniff test; "
        "StudyForge therefore privileges instrumentation—logs, explicit states, reproducible seeds—over glossy demos."
    ),
    (
        "Human-in-the-loop evaluation remains the gold standard for educational NLP when stakes involve comprehension. "
        "Expert annotators can score whether an answer faithfully reflects cited passages; novice learners can rank "
        "explanations for clarity; instructors can audit graph summaries against lecture intent. Automating these "
        "judgments entirely is premature; instead, tooling should make audits cheap enough to happen routinely."
    ),
]


S4_2 = [
    (
        "Operational guardrails include structured logging with correlation IDs, explicit configuration errors when "
        "graph extraction lacks credentials, and UI surfaces that communicate indexing state. These guardrails reduce "
        "support burden during pilots and prevent silent degradation where answers appear fluent but evidence sets "
        "shrink unnoticed."
    ),
]


S4_2_BULLETS = [
        "Contract tests catch accidental route drift during refactors.",
        "Streaming parsers should tolerate partial failures without wedging sessions.",
        "Access controls remain coarse by default—deployment-specific hardening stays operator responsibility.",
]


S4_3 = [
    (
        "Many grading demonstrations execute without shared secrets on lab machines. StudyForge therefore ships mock "
        "panels that mirror citation placeholders and configuration dialogs without invoking production models. Figures "
        "8–9 document this stance explicitly; Figures 10–11 (Section 6) illustrate fully configured deployments where hybrid chat, "
        "graph visualization, and agent examination flows align with the narratives above."
    ),
]


S4_4 = [
    (
        "Independent replication remains the credibility backbone of applied ML systems—even when demonstrations dazzle "
        "live audiences. Reviewers should insist on frozen dependency manifests, pinned model endpoints or offline "
        "weights where feasible, and hashed corpora snapshots so retrieval evaluations compare apples-to-apples across "
        "commits."
    ),
    (
        "Checklists help: confirm ingestion statuses transition from pending to completed; verify graph entity counts "
        "move monotonically upward after lawful uploads; capture latency percentiles rather than single-shot timings "
        "during Wi-Fi contention; archive prompts alongside outputs because identical temperatures still drift when "
        "providers silently upgrade routing."
    ),
    (
        "Qualitative audits deserve structured rubrics—coverage (did answers cite relevant passages?), faithfulness "
        "(did paraphrases distort definitions?), calibration (did the UI communicate uncertainty?). Numeric dashboards "
        "without rubrics invite Goodhart-style gaming."
    ),
    (
        "Ethically, replication packets should scrub personally identifiable information from exercise uploads unless "
        "consent pathways exist. StudyForge’s separation of uploads and traces simplifies redaction workflows relative "
        "to monolithic LMS dumps."
    ),
]


S4_4_BULLETS = [
    "Publish environment templates alongside README instructions.",
    "Record corpus checksums; note slide edits between experimental trials.",
    "Log provider identifiers but never API secrets in shared artifacts.",
    "Capture retrieval mode, temperature, and max-token settings per session.",
    "Store anonymized chat transcripts only under institutional policy.",
    "Run contract tests in CI even when full GPU pipelines cannot execute continuously.",
    "Document manual correction steps applied after OCR failures.",
    "Version visual assets in reports when UI iterations affect reader interpretation.",
]


S5_1_BULLETS = [
    "Graph-augmented retrieval couples lexical similarity with relational cues, improving answer coherence beyond flat "
    "top-k chunking alone.",
    "Multi-modal document ingestion respects slide/page semantics typical of instruction while remaining extensible.",
    "Operational intelligence: modular agents, streaming protocols, and explicit retrieval modes reduce opaque failures.",
    "Provider interchangeability via OpenAI-compatible bindings lowers switching costs as model economics evolve.",
    "Assessment-aware tooling connects corpus signals to exam workflows instead of treating tutoring and testing as "
    "disjoint silos.",
]


S5_2 = [
    (
        "StudyForge contributes an integrated blueprint—from ingestion through hybrid retrieval to visualization and "
        "exam-oriented automation—that teams can reproduce without bespoke infrastructure. It demonstrates that "
        "LightRAG-class pipelines can be packaged behind disciplined APIs and credible UX patterns suitable for "
        "course-scale pilots rather than toy demos."
    ),
    (
        "Beyond immediate utility, the project is a case study in separation of concerns: embeddings index evidence, "
        "graphs summarize conceptual fabric, chat models narrate within constraints, and agents orchestrate workloads "
        "that would otherwise sprawl across unmaintainable scripts. That decomposition is the lasting engineering "
        "lesson for intelligent learning systems built on rapidly changing foundation models."
    ),
]


S5_3 = [
    (
        "Single-course pilots impose modest concurrency: dozens of simultaneous chat turns, indexing jobs serialized per "
        "subject, embeddings batched within conservative rate limits. StudyForge’s defaults reflect that envelope—"
        "parallelism sufficient for seminar-scale classrooms without enterprise orchestrators."
    ),
    (
        "Departmental scaling introduces qualitatively different demands: shared GPU pools, quota fairness across "
        "sections, centralized auditing, and SSO-aware access boundaries. The modular FastAPI surface aids incremental "
        "hardening—authentication middleware, per-tenant storage prefixes, background workers—but full multi-tenant SaaS "
        "robustness remains future engineering rather than claimed present capability."
    ),
    (
        "Cost envelopes fluctuate with embedding dimensionalities, graph extraction aggressiveness, and chat streaming "
        "lengths. Operators should budget separately for cold-start indexing (burst spend) versus steady-state querying "
        "(amortized per student-hour). Transparent dashboards tying token usage to subject IDs prevent silent budget "
        "overruns mid-semester."
    ),
    (
        "Latency envelopes likewise bifurcate: interactive tutoring tolerates seconds-scale retrieval if prose streams "
        "immediately afterward; batch exam analytics tolerate minutes if progress bars remain truthful. Architectural "
        "clarity about which path is which prevents mis-setting timeouts that truncate pedagogically critical outputs."
    ),
    (
        "Finally, organizational envelopes encompass policy: institutions embracing BYOK (bring-your-own-key) models "
        "align spend with departmental priorities while preserving vendor flexibility; those requiring air-gapped "
        "deployments lean on local embeddings and quantized chat models—tradeoffs StudyForge’s binding layers attempt to "
        "accommodate without dictating a single hosting story."
    ),
]


S5_3_BULLETS = [
    "Pilot phase: prioritize citation fidelity and instructor trust over peak concurrency.",
    "Growth phase: introduce quotas, backoff strategies, and staged indexing queues.",
    "Governance phase: formalize data retention, export, and deletion workflows per jurisdiction.",
    "Economic phase: monitor embedding-token dominance versus chat-token dominance in monthly statements.",
    "Reliability phase: practice failover scripts when remote APIs degrade during finals week.",
    "Pedagogy phase: co-design usage policies with curriculum committees—not only IT stakeholders.",
]

