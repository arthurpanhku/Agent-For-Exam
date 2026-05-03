#!/usr/bin/env python3
"""
Regenerate Figure 10 (chat + knowledge graph) and Figure 11 (RAG-bound variant questions)
for docs/report_en_assets/, using a running StudyForge stack.

LLM: DeepSeek official OpenAI-compatible HTTPS API per https://api-docs.deepseek.com/
    - base URL for StudyForge host field: https://api.deepseek.com
    - chat path is appended as /chat/completions by the backend
    - recommended models include deepseek-v4-flash / deepseek-v4-pro (see docs)

Embedding for LightRAG indexing is still required: default script expects SiliconFlow
(OpenAI-compatible embedding at api.siliconflow.cn) unless you already configured
embedding via the Settings UI.

Environment:
  DEEPSEEK_API_KEY   — required for chat + knowledge-graph extraction bindings
  SILICONFLOW_API_KEY — recommended for embedding binding (subject document indexing)
  STUDYFORGE_API_KEY — optional; sent as X-API-Key if the API gateway requires it

Tip: Cursor Agent subprocesses may not see tokens you only export in a local terminal.
Put secrets in `backend/.env` (gitignored) so scripts can load them via python-dotenv:

  DEEPSEEK_API_KEY=...
  SILICONFLOW_API_KEY=...

If you use Claude Code / Anthropic SDK against DeepSeek (`ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic`),
you can reuse the same secret in this repo: `scripts/capture_report_figures_10_11.py` and `verify_deepseek_openai_sdk.py`
will treat `ANTHROPIC_AUTH_TOKEN` as `DEEPSEEK_API_KEY` when the latter is unset, and map `ANTHROPIC_*_MODEL` to
`DEEPSEEK_MODEL` after stripping accidental ANSI suffixes like `[1m`.

StudyForge itself still configures the OpenAI-compatible host `https://api.deepseek.com` (not `/anthropic`).

Typical run (from repo root Agent-For-Exam/Agent-For-Exam):

  export DEEPSEEK_API_KEY=...
  export SILICONFLOW_API_KEY=...
  ./frontend/node_modules/.bin/vite build   # not required if dev servers already up
  python3 scripts/capture_report_figures_10_11.py --frontend-url http://127.0.0.1:5173 \\
      --api-url http://127.0.0.1:8010

Prerequisites: backend + Vite dev server running; Playwright Chromium installed
(`playwright install chromium` if needed).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/report_en_assets"
DEMO_PPTX = ASSETS / "_capture_demo.pptx"

FIG10 = ASSETS / "user_feat_rag_knowledge_graph.png"
FIG11 = ASSETS / "user_feat_agent_exam_generation.png"


def load_env_files(extra: Path | None = None) -> None:
    """Load DEEPSEEK_API_KEY etc. from disk — Cursor Agent shells often do not inherit IDE env vars."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    if extra is not None and extra.is_file():
        load_dotenv(extra, override=True)
    for path in (ROOT / "backend" / ".env", ROOT / ".env", Path.home() / ".studyforge.env"):
        if path.is_file():
            load_dotenv(path, override=False)


def _sanitize_model_name(raw: str) -> str:
    """Strip accidental ANSI / terminal artifacts from pasted model names (e.g. deepseek-v4-pro[1m)."""
    if not raw:
        return raw
    s = re.sub(r"\x1b\[[0-9;]*m", "", raw)
    s = re.sub(r"\[[0-9;]*m", "", s)
    return s.strip()


def normalize_deepseek_aliases() -> None:
    """Align Claude Code / DeepSeek Anthropic-style env with StudyForge capture helpers."""
    if not (os.environ.get("DEEPSEEK_API_KEY") or "").strip():
        anth = (os.environ.get("ANTHROPIC_AUTH_TOKEN") or "").strip()
        if anth:
            os.environ["DEEPSEEK_API_KEY"] = anth

    if not (os.environ.get("DEEPSEEK_MODEL") or "").strip():
        for key in (
            "ANTHROPIC_MODEL",
            "ANTHROPIC_DEFAULT_OPUS_MODEL",
            "ANTHROPIC_DEFAULT_SONNET_MODEL",
            "ANTHROPIC_DEFAULT_HAIKU_MODEL",
        ):
            candidate = _sanitize_model_name((os.environ.get(key) or "").strip())
            if candidate:
                os.environ["DEEPSEEK_MODEL"] = candidate
                break


def _headers() -> dict[str, str]:
    h: dict[str, str] = {}
    gate = (os.environ.get("STUDYFORGE_API_KEY") or os.environ.get("AFE_API_KEY") or "").strip()
    if gate:
        h["X-API-Key"] = gate
    return h


def configure_deepseek(client: httpx.Client, api_key: str, model: str) -> None:
    """Bind chat / KG / mindmap to DeepSeek OpenAI-compatible endpoint."""
    host = "https://api.deepseek.com"
    payload = {
        "binding": "openai",
        "host": host,
        "model": model,
        "api_key": api_key,
    }
    for scene in ("chat", "knowledge_graph", "mindmap"):
        r = client.post(f"/api/settings/llm-config/{scene}", json=payload)
        r.raise_for_status()


def configure_siliconflow_embedding(client: httpx.Client, api_key: str) -> None:
    r = client.post(
        "/api/settings/llm-config/embedding",
        json={
            "binding": "siliconflow",
            "host": "https://api.siliconflow.cn/v1",
            "model": "Qwen/Qwen3-Embedding-0.6B",
            "api_key": api_key,
        },
    )
    r.raise_for_status()


def create_subject_and_conversation(client: httpx.Client) -> tuple[str, str]:
    r = client.post("/api/subjects", json={"name": "Report capture", "description": "auto"})
    r.raise_for_status()
    subject_id = r.json()["subject_id"]
    r = client.post(
        f"/api/subjects/{subject_id}/conversations",
        json={"title": "Figure capture", "conversation_type": "chat"},
    )
    r.raise_for_status()
    conversation_id = r.json()["conversation_id"]
    return subject_id, conversation_id


def upload_pptx(client: httpx.Client, subject_id: str, pptx_path: Path) -> str:
    with pptx_path.open("rb") as f:
        files = {"files": (pptx_path.name, f, "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
        r = client.post(f"/api/subjects/{subject_id}/documents/upload", files=files)
    r.raise_for_status()
    uploaded = r.json()["uploaded_files"][0]
    return uploaded["file_id"]


def wait_document_ready(client: httpx.Client, subject_id: str, file_id: str, timeout_sec: int = 900) -> None:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        rr = client.get(f"/api/subjects/{subject_id}/documents/{file_id}/status")
        rr.raise_for_status()
        st = rr.json().get("status")
        if st == "completed":
            return
        if st == "failed":
            raise RuntimeError(rr.json().get("error") or "document processing failed")
        time.sleep(3)
    raise TimeoutError("document indexing timed out")


def fetch_variant_questions(client: httpx.Client, conversation_id: str) -> dict[str, Any]:
    r = client.post(
        f"/api/conversations/{conversation_id}/variant-questions",
        json={
            "topic": "Tony Lam, AlgoGene, and trading competitions mentioned in the slides",
            "mode": "mix",
            "count": 4,
            "base_difficulty": "medium",
        },
        timeout=180.0,
    )
    r.raise_for_status()
    return r.json()


def write_variant_html(data: dict[str, Any], out_html: Path) -> None:
    qs = data.get("questions") or []
    rows = []
    for i, q in enumerate(qs, start=1):
        opts = q.get("options") or []
        opt_txt = "".join(f"<li>{o}</li>" for o in opts)
        rows.append(
            f"""
            <div class="card">
              <div class="qid">GEN_{i:03d}</div>
              <div class="stem">{q.get("stem", "")}</div>
              <ul class="opts">{opt_txt}</ul>
              <div class="answer"><strong>答案：</strong>{q.get("answer", "")}</div>
              <div class="meta">
                题型：单选题 · 难度：{q.get("difficulty", "—")} · Bloom：{q.get("bloom_level", "—")}
                · 命题说明：{q.get("rationale", "")}
              </div>
            </div>
            """
        )
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>变式题生成 · StudyForge</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background: #f0f2f5;
      margin: 0;
      padding: 24px;
      color: #1f2937;
    }}
    h1 {{ font-size: 18px; margin: 0 0 12px 0; }}
    .banner {{
      background: #e8f8ef;
      border: 1px solid #b7eb8f;
      border-radius: 8px;
      padding: 12px 16px;
      margin-bottom: 16px;
      font-size: 14px;
    }}
    .card {{
      background: #fff;
      border-radius: 10px;
      padding: 16px 18px;
      margin-bottom: 14px;
      box-shadow: 0 1px 2px rgba(0,0,0,.06);
      border: 1px solid #e5e7eb;
    }}
    .qid {{ font-weight: 700; color: #2563eb; margin-bottom: 8px; }}
    .stem {{ line-height: 1.55; white-space: pre-wrap; }}
    .opts {{ margin: 10px 0 8px 18px; }}
    .answer {{ margin-top: 8px; }}
    .meta {{ margin-top: 10px; font-size: 12px; color: #6b7280; }}
    .foot {{
      margin-top: 20px;
      font-size: 12px;
      color: #9ca3af;
    }}
  </style>
</head>
<body>
  <h1>生成结果（变式题 · 绑定讲义检索）</h1>
  <div class="banner">
    成功生成 {len(qs)} 道试题 · Chat LLM：DeepSeek OpenAI-compatible API（参见 https://api-docs.deepseek.com/）
    · 检索模式：{data.get("mode", "mix")}
  </div>
  {"".join(rows)}
  <p class="foot">StudyForge · scripts/capture_report_figures_10_11.py · 用于报告 Figure 11</p>
</body>
</html>
"""
    out_html.write_text(html, encoding="utf-8")


def screenshot_fig10(chat_url: str) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1480, "height": 920})
        page.goto(chat_url, wait_until="networkidle", timeout=120_000)
        page.wait_for_selector("textarea.chat-input", timeout=60_000)
        page.fill(
            "textarea.chat-input",
            "Based on the uploaded slides: summarize Tony Lam, AlgoGene, and the competitions mentioned. Use citations if shown.",
        )
        page.click("button.send-btn")
        page.wait_for_timeout(5000)
        page.wait_for_function(
            """() => {
              const blocks = document.querySelectorAll('.message.assistant-message');
              const last = blocks[blocks.length - 1];
              if (!last) return false;
              const t = (last.innerText || '').trim();
              return t.length > 120;
            }""",
            timeout=240_000,
        )
        page.wait_for_timeout(2000)
        page.get_by_role("tab", name="Documents").click()
        page.wait_for_timeout(1500)
        page.wait_for_selector('button:has-text("查看知识图谱")', timeout=60_000)
        page.get_by_role("button", name="查看知识图谱").click()
        page.wait_for_timeout(5000)
        page.screenshot(path=str(FIG10), full_page=False)
        browser.close()


def screenshot_fig11_html(html_path: Path) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1100, "height": 1200})
        page.goto(html_path.as_uri(), wait_until="load")
        page.wait_for_timeout(800)
        page.screenshot(path=str(FIG11), full_page=True)
        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture Figure 10–11 for the EN report.")
    parser.add_argument("--api-url", default=os.environ.get("STUDYFORGE_API_URL", "http://127.0.0.1:8010"))
    parser.add_argument("--frontend-url", default=os.environ.get("STUDYFORGE_FRONTEND_URL", "http://127.0.0.1:5173"))
    parser.add_argument("--env-file", type=Path, default=None, help="Optional .env path (loaded first).")
    parser.add_argument(
        "--deepseek-model",
        default=None,
        help="Overrides DEEPSEEK_MODEL / ANTHROPIC_* aliases; see https://api-docs.deepseek.com/",
    )
    parser.add_argument("--skip-config", action="store_true", help="Do not POST /api/settings (reuse UI config).")
    args = parser.parse_args()

    load_env_files(args.env_file)
    normalize_deepseek_aliases()

    chosen_model = args.deepseek_model or os.environ.get("DEEPSEEK_MODEL") or "deepseek-v4-pro"
    chosen_model = _sanitize_model_name(chosen_model.strip())

    ds_key = (os.environ.get("DEEPSEEK_API_KEY") or "").strip()
    sf_key = (os.environ.get("SILICONFLOW_API_KEY") or "").strip()
    if not ds_key:
        print(
            "Missing DEEPSEEK_API_KEY (set it or ANTHROPIC_AUTH_TOKEN for Claude Code–style DeepSeek env).\n"
            "Docs: https://api-docs.deepseek.com/ — StudyForge uses OpenAI-compatible https://api.deepseek.com",
            file=sys.stderr,
        )
        sys.exit(2)
    if not sf_key and not args.skip_config:
        print(
            "Missing SILICONFLOW_API_KEY (needed for default embedding binding).\n"
            "Export it, or re-run with --skip-config if embedding is already configured in Settings.",
            file=sys.stderr,
        )
        sys.exit(2)

    if not DEMO_PPTX.exists():
        print(f"Missing demo deck {DEMO_PPTX}. Run the pptx bootstrap or restore the file.", file=sys.stderr)
        sys.exit(2)

    ASSETS.mkdir(parents=True, exist_ok=True)

    base_headers = _headers()
    with httpx.Client(base_url=args.api_url.rstrip("/"), headers=base_headers, timeout=120.0) as client:
        if not args.skip_config:
            configure_deepseek(client, ds_key, chosen_model)
            if sf_key:
                configure_siliconflow_embedding(client, sf_key)

        subject_id, conversation_id = create_subject_and_conversation(client)
        file_id = upload_pptx(client, subject_id, DEMO_PPTX)
        wait_document_ready(client, subject_id, file_id)

        variant_payload = fetch_variant_questions(client, conversation_id)
        html_tmp = ASSETS / "_fig11_variant_preview.html"
        write_variant_html(variant_payload, html_tmp)

        chat_url = f"{args.frontend_url.rstrip('/')}/subject/{subject_id}/chat/{conversation_id}"

    try:
        screenshot_fig10(chat_url)
        screenshot_fig11_html(html_tmp)
    except ImportError:
        print("Playwright Python package missing. pip install playwright && playwright install chromium", file=sys.stderr)
        sys.exit(3)
    except Exception as exc:
        print(f"Screenshot step failed: {exc}", file=sys.stderr)
        sys.exit(4)

    print(f"Wrote {FIG10}\nWrote {FIG11}")


if __name__ == "__main__":
    main()
