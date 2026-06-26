#!/usr/bin/env python3
"""Optional regression against the accepted 影像基础参数 project artifacts."""

from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


FORBIDDEN = [
    "PDF", "原稿", "来源文档", "制作说明", "图旁注明", "详细讲稿", "预计讲解时间",
    "对应节点", "本页顺序", "本页内容", "来源路径", "screen_evidence", "coverage_note",
    "Genji 是真想教会你",
]


def pptx_visible_text(path: Path) -> tuple[int, str]:
    with zipfile.ZipFile(path) as archive:
        slides = [name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)]
        text: list[str] = []
        for name in slides:
            xml = archive.read(name).decode("utf-8", errors="replace")
            text.extend(html.unescape(value) for value in re.findall(r"<a:t>(.*?)</a:t>", xml, flags=re.S))
        return len(slides), "\n".join(text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, type=Path)
    args = parser.parse_args()
    project = args.project_root.expanduser().resolve()
    course = project / "课件"
    pptx = course / "影像基础参数-Canva导入稿.pptx"
    xmind = course / "影像基础参数.xmind"
    pdf = course / "影像基础参数.pdf"
    for path in (pptx, xmind, pdf):
        if not path.is_file():
            raise SystemExit(f"missing golden artifact: {path}")
    count, text = pptx_visible_text(pptx)
    if count != 44:
        raise SystemExit(f"expected 44 golden slides, got {count}")
    found = [term for term in FORBIDDEN if term.lower() in text.lower()]
    if found:
        raise SystemExit(f"golden PPTX contains forbidden learner text: {found}")
    extract = Path(__file__).resolve().parents[1] / "skills" / "build-course-canva-deck" / "scripts" / "extract_source.py"
    with tempfile.TemporaryDirectory(prefix="golden-course-deck-") as raw:
        temp = Path(raw)
        for source in (xmind, pdf):
            output = temp / f"{source.suffix.lstrip('.')}-source-map.json"
            result = subprocess.run(
                [sys.executable, str(extract), "--input", str(source), "--output", str(output)],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            if result.returncode:
                raise SystemExit(result.stderr or result.stdout)
            if output.stat().st_size < 1000:
                raise SystemExit(f"source extraction unexpectedly small: {source}")
    print("golden regression passed: 44 slides, zero forbidden learner terms, XMind/PDF extraction succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
