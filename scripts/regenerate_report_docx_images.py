#!/usr/bin/env python3
"""Replace embedded PNGs in the Final Project Report docx with Graphviz / Pillow diagrams.

Large figures use DOT (Mermaid-equivalent flow semantics). Small inline icons are 20×20 PIL glyphs.
"""
from __future__ import annotations

import io
import shutil
import struct
import subprocess
import tempfile
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

REPO = "https://github.com/arthurpanhku/studyforge"

ROOT = Path(__file__).resolve().parents[1]
DOC_IN = ROOT / "docs/Final_Project_Report_Intelligent_Learning_Assistant_LightRAG_Agent_updated.docx"
DOC_OUT = DOC_IN  # overwrite canonical copy


def png_pixel_size(data: bytes) -> tuple[int, int] | None:
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", data[16:24])


def dot_to_png(dot: str, out_path: Path, target_wh: tuple[int, int] | None = None) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["dot", "-Tpng", "-o", str(out_path)],
        input=dot.encode("utf-8"),
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="replace") or "dot failed")
    if target_wh:
        w, h = target_wh
        im = Image.open(out_path).convert("RGBA")
        im = im.resize((w, h), Image.Resampling.LANCZOS)
        bg = Image.new("RGB", (w, h), (255, 255, 255))
        bg.paste(im, mask=im.split()[3] if im.mode == "RGBA" else None)
        bg.save(out_path, format="PNG", optimize=True)


def hsl_to_rgb(h: float, s: float, l: float) -> tuple[int, int, int]:
    h /= 360.0
    if s == 0:
        v = int(l * 255)
        return v, v, v
    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    def hue2rgb(p, q, t):
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p
    r = hue2rgb(p, q, h + 1 / 3)
    g = hue2rgb(p, q, h)
    b = hue2rgb(p, q, h - 1 / 3)
    return int(r * 255), int(g * 255), int(b * 255)


def tiny_icon(index: int, out_path: Path, size: tuple[int, int] = (20, 20)) -> None:
    w, h = size
    hue = (index * 41 + 180) % 360
    fill = hsl_to_rgb(hue, 0.45, 0.55)
    border = hsl_to_rgb(hue, 0.55, 0.35)
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    pad_x = max(1, w // 10)
    pad_y = max(1, h // 10)
    draw.ellipse(
        (pad_x, pad_y, w - pad_x - 1, h - pad_y - 1),
        fill=fill + (255,),
        outline=border + (255,),
        width=1,
    )
    img.save(out_path, format="PNG")


def diagram_image17(path: Path, wh: tuple[int, int]) -> None:
    dot = rf"""
digraph G {{
  graph [fontname="Helvetica", fontsize=11, bgcolor=white, pad=0.3, rankdir=TB];
  node [fontname="Helvetica", fontsize=10, shape=box, style="rounded,filled", fillcolor="#E8F4FF", color="#409EFF"];
  edge [fontname="Helvetica", fontsize=9, color="#606266"];

  labelloc="t";
  label="StudyForge · layered architecture (diagram replaces UI screenshot)\\nRepo: {REPO}";

  UI [label="Vue 3 + Element Plus\\nChat · KG · exams · documents"];
  API [label="FastAPI backend\\nstreaming query · conversations · tools"];
  LKG [label="LightRAG core\\nchunking · embeddings · KG + vectors"];
  AG [label="Agent orchestration\\nquery_knowledge_graph · citations · variants"];
  LLM [label="Configured LLM\\nchat + extraction"];

  UI -> API -> LKG -> LLM;
  API -> AG -> LKG [style=dashed, label="tools"];
}}
"""
    dot_to_png(dot, path, wh)


def diagram_image24(path: Path, wh: tuple[int, int]) -> None:
    dot = """
digraph G {
  graph [fontname="Helvetica", fontsize=11, bgcolor=white, pad=0.3, rankdir=LR];
  node [fontname="Helvetica", fontsize=10, shape=box, style="rounded,filled", fillcolor="#F0F9EB", color="#67C23A"];
  edge [fontname="Helvetica", fontsize=9];

  label="Knowledge graph exploration (semantic diagram)";
  U [label="User"];
  Z [label="Zoom / pan\\nviewport"];
  F [label="Filter\\nsection · entity type"];
  S [label="Focused subgraph\\nCytoscape.js"];

  U -> Z -> S;
  U -> F -> S;
}
"""
    dot_to_png(dot, path, wh)


def diagram_image28(path: Path, wh: tuple[int, int]) -> None:
    dot = """
digraph G {
  graph [fontname="Helvetica", fontsize=11, bgcolor=white, pad=0.3, rankdir=TB];
  node [fontname="Helvetica", fontsize=10, shape=box, style="rounded,filled", fillcolor="#FFF7E6", color="#E6A23C"];
  edge [fontname="Helvetica", fontsize=9];

  label="MCQ / Agent pipeline · quality gates (flowchart)";
  D [label="Retrieved chunks\\n(RAG context)"];
  E [label="Exam samples\\ncurriculum alignment"];
  A [label="Multi-Agent\\ngenerator"];
  Q [label="QC\\nschema · logic · dedup"];

  D -> A;
  E -> A;
  A -> Q [label="publish when OK"];
}
"""
    dot_to_png(dot, path, wh)


def diagram_image32(path: Path, wh: tuple[int, int]) -> None:
    dot = """
digraph G {
  graph [fontname="Helvetica", fontsize=11, bgcolor=white, pad=0.3, rankdir=LR];
  node [fontname="Helvetica", fontsize=10, shape=box, style="rounded,filled", fillcolor="#F4F4F5", color="#909399"];
  edge [fontname="Helvetica", fontsize=9];

  label="Grading · persistence (data flow)";
  G [label="Per-item grading\\nobj + LLM rubric"];
  S [label="Store row\\nanswer · ref · score · feedback"];
  L [label="Learning record\\nfuture analytics"];

  G -> S -> L;
}
"""
    dot_to_png(dot, path, wh)


def diagram_image33(path: Path, wh: tuple[int, int]) -> None:
    dot = """
digraph G {
  graph [fontname="Helvetica", fontsize=11, bgcolor=white, pad=0.3, rankdir=LR];
  node [fontname="Helvetica", fontsize=10, shape=box, style="rounded,filled", fillcolor="#ECF5FF", color="#409EFF"];
  edge [fontname="Helvetica", fontsize=9];

  label="Exam attempts → longitudinal dataset";
  A [label="Single attempt\\nscores + items"];
  R [label="Rollups\\nper topic · difficulty"];
  D [label="Consistent dataset\\nfor tracking"];

  A -> R -> D;
}
"""
    dot_to_png(dot, path, wh)


def diagram_image36(path: Path, wh: tuple[int, int]) -> None:
    dot = """
digraph G {
  graph [fontname="Helvetica", fontsize=11, bgcolor=white, pad=0.3, rankdir=TB];
  node [fontname="Helvetica", fontsize=10, shape=box, style="rounded,filled", fillcolor="#FCE8F3", color="#F56C6C"];
  edge [fontname="Helvetica", fontsize=9];

  label="Closed-loop learning visualization";
  V [label="Charts\\ntimeline · radar · heatmap"];
  H [label="Agent-style recommendations\\nweak areas · drills"];
  N [label="Next study actions"];

  V -> H -> N;
  N -> V [label="new results", style=dashed];
}
"""
    dot_to_png(dot, path, wh)


def main() -> None:
    if not DOC_IN.exists():
        raise SystemExit(f"Missing {DOC_IN}")

    tmp = Path(tempfile.mkdtemp(prefix="studyforge_docx_img_"))
    try:
        generated: dict[str, Path] = {}

        with zipfile.ZipFile(DOC_IN, "r") as zin:
            media_files = sorted(
                n for n in zin.namelist() if n.startswith("word/media/image") and n.endswith(".png")
            )
            targets: dict[str, tuple[int, int]] = {}
            for name in media_files:
                data = zin.read(name)
                wh = png_pixel_size(data)
                if not wh:
                    continue
                targets[name.split("/")[-1]] = wh

        # Large narrative diagrams
        diagram_image17(tmp / "image17.png", targets["image17.png"])
        diagram_image24(tmp / "image24.png", targets["image24.png"])
        diagram_image28(tmp / "image28.png", targets["image28.png"])
        diagram_image32(tmp / "image32.png", targets["image32.png"])
        diagram_image33(tmp / "image33.png", targets["image33.png"])
        diagram_image36(tmp / "image36.png", targets["image36.png"])
        for k in ["image17.png", "image24.png", "image28.png", "image32.png", "image33.png", "image36.png"]:
            generated[k] = tmp / k

        # Small icons: deterministic hue by image index
        for fname, wh in targets.items():
            if fname in generated:
                continue
            idx = int(fname.replace("image", "").replace(".png", ""))
            p = tmp / fname
            tiny_icon(idx, p, wh)
            generated[fname] = p

        final_bytes = io_zip_replace_media(DOC_IN, generated)
        DOC_OUT.write_bytes(final_bytes)
        print(f"Wrote {DOC_OUT} ({len(generated)} PNGs replaced)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def io_zip_replace_media(doc_path: Path, media_map: dict[str, Path]) -> bytes:
    """Return new docx bytes with word/media/<file> replaced from disk paths."""
    out = io.BytesIO()
    with zipfile.ZipFile(doc_path, "r") as zin, zipfile.ZipFile(
        out, "w", compression=zipfile.ZIP_DEFLATED
    ) as zout:
        for item in zin.infolist():
            name = item.filename
            base = name.split("/")[-1] if "/" in name else name
            payload = (
                media_map[base].read_bytes()
                if name.startswith("word/media/") and base in media_map
                else zin.read(name)
            )
            zout.writestr(name, payload, compress_type=zipfile.ZIP_DEFLATED)
    return out.getvalue()


if __name__ == "__main__":
    main()
