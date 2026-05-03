#!/usr/bin/env python3
"""Minimal DeepSeek check using the official OpenAI-compatible SDK (see https://api-docs.deepseek.com/).

Loads optional env files first — same as capture_report_figures_10_11.py — because Cursor Agent
processes often do not inherit shell-exported DEEPSEEK_API_KEY.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _sanitize_model_name(raw: str) -> str:
    if not raw:
        return raw
    s = re.sub(r"\x1b\[[0-9;]*m", "", raw)
    s = re.sub(r"\[[0-9;]*m", "", s)
    return s.strip()


def normalize_deepseek_aliases() -> None:
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


def load_env_files(extra: Path | None = None) -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        load_dotenv = None  # type: ignore
    if load_dotenv is None:
        return
    if extra is not None and extra.is_file():
        load_dotenv(extra, override=True)
    for path in (ROOT / "backend" / ".env", ROOT / ".env", Path.home() / ".studyforge.env"):
        if path.is_file():
            load_dotenv(path, override=False)


def main() -> None:
    extra = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
    load_env_files(extra)
    normalize_deepseek_aliases()

    key = (os.environ.get("DEEPSEEK_API_KEY") or "").strip()
    if not key:
        print(
            "DEEPSEEK_API_KEY / ANTHROPIC_AUTH_TOKEN not found. Add one to backend/.env or:\n"
            "  python3 scripts/verify_deepseek_openai_sdk.py /path/to/.env",
            file=sys.stderr,
        )
        sys.exit(2)

    try:
        from openai import OpenAI
    except ImportError:
        print("Install: pip install openai", file=sys.stderr)
        sys.exit(3)

    client = OpenAI(api_key=key, base_url="https://api.deepseek.com")
    model = _sanitize_model_name((os.environ.get("DEEPSEEK_MODEL") or "deepseek-v4-pro").strip())
    kwargs = dict(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Reply with exactly: DeepSeek OK"},
        ],
        stream=False,
    )
    try:
        response = client.chat.completions.create(
            **kwargs,
            reasoning_effort="high",
            extra_body={"thinking": {"type": "enabled"}},
        )
    except TypeError:
        response = client.chat.completions.create(**kwargs)
    text = (response.choices[0].message.content or "").strip()
    preview = text.replace("\n", " ")[:400]
    print("deepseek_ok:", preview)


if __name__ == "__main__":
    main()
