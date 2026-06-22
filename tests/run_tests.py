#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "build-course-canva-deck"
SCRIPTS = SKILL / "scripts"
FIXTURES = ROOT / "tests" / "fixtures"


def run(command: list[str], *, expect: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != expect:
        print("COMMAND:", " ".join(command))
        print("STDOUT:\n", result.stdout)
        print("STDERR:\n", result.stderr)
        raise AssertionError(f"expected exit {expect}, got {result.returncode}")
    return result


def audit(temp: Path, deck: Path, source: Path, *, expect: int = 0) -> dict:
    report = temp / f"{deck.stem}-report.json"
    run(
        [sys.executable, str(SCRIPTS / "audit_deck.py"), "--deck-spec", str(deck), "--source-map", str(source), "--report", str(report)],
        expect=expect,
    )
    return json.loads(report.read_text(encoding="utf-8"))


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="course-canva-skill-") as raw:
        temp = Path(raw)

        # Source extraction preserves order and refuses to infer outline mode.
        source_map = temp / "source-map.json"
        run([sys.executable, str(SCRIPTS / "extract_source.py"), "--input", str(FIXTURES / "detailed-outline.md"), "--output", str(source_map)])
        extracted = json.loads(source_map.read_text(encoding="utf-8"))
        assert extracted["outline_mode"] is None
        assert extracted["requires_user_outline_mode"] is True
        run([sys.executable, str(SCRIPTS / "validate_source_map.py"), str(source_map), "--require-mode"], expect=1)
        run([sys.executable, str(SCRIPTS / "validate_source_map.py"), str(source_map), "--mode", "detailed", "--write", "--require-mode"])

        # Modern XMind parsing works and also leaves mode unset.
        xmind = temp / "fixture.xmind"
        with zipfile.ZipFile(xmind, "w") as archive:
            archive.writestr("content.json", json.dumps([{"rootTopic": {"title": "根节点", "children": {"attached": [{"title": "子节点"}]}}}], ensure_ascii=False))
        xmind_map = temp / "xmind-map.json"
        run([sys.executable, str(SCRIPTS / "extract_source.py"), "--input", str(xmind), "--output", str(xmind_map)])
        assert [node["text"] for node in json.loads(xmind_map.read_text(encoding="utf-8"))["nodes"]] == ["根节点", "子节点"]

        # Detailed baseline passes; added content does not.
        detailed = audit(temp, FIXTURES / "deck-spec-detailed.json", FIXTURES / "source-map-detailed.json")
        assert detailed["ok"]
        detailed_bad_path = temp / "detailed-added.json"
        detailed_bad = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
        detailed_bad["slides"][1]["added_content"] = [{"text": "额外流程"}]
        detailed_bad_path.write_text(json.dumps(detailed_bad, ensure_ascii=False), encoding="utf-8")
        assert not audit(temp, detailed_bad_path, FIXTURES / "source-map-detailed.json", expect=1)["ok"]

        # Sparse direct expansion passes.
        sparse = audit(temp, FIXTURES / "deck-spec-sparse.json", FIXTURES / "source-map-sparse.json")
        assert sparse["ok"]

        # Low-relevance software operation and backstage wording both fail.
        sparse_bad_path = temp / "sparse-out-of-scope.json"
        sparse_bad = json.loads((FIXTURES / "deck-spec-sparse.json").read_text(encoding="utf-8"))
        sparse_bad["slides"][1]["screen"]["bullets"].append("进入剪辑软件操作界面")
        sparse_bad["slides"][1]["added_content"].append({
            "text": "剪辑软件操作", "source_node_id": "n0002", "kind": "example",
            "relevance": "low", "evidence_urls": ["https://example.com"],
        })
        sparse_bad_path.write_text(json.dumps(sparse_bad, ensure_ascii=False), encoding="utf-8")
        bad_report = audit(temp, sparse_bad_path, FIXTURES / "source-map-sparse.json", expect=1)
        assert any("out-of-scope" in error or "not directly relevant" in error for error in bad_report["errors"])

        backstage_path = temp / "backstage.json"
        backstage = json.loads((FIXTURES / "deck-spec-detailed.json").read_text(encoding="utf-8"))
        backstage["slides"][1]["screen"]["explanation"] += " 在 PDF 中这样描述。"
        backstage_path.write_text(json.dumps(backstage, ensure_ascii=False), encoding="utf-8")
        backstage_report = audit(temp, backstage_path, FIXTURES / "source-map-detailed.json", expect=1)
        assert any("PDF" in error for error in backstage_report["errors"])

        # Contact-sheet helper works with generated PNGs.
        try:
            from PIL import Image
        except ImportError:
            Image = None
        if Image:
            image_dir = temp / "images"
            image_dir.mkdir()
            for number in range(1, 4):
                Image.new("RGB", (320, 180), (number * 40, 30, 20)).save(image_dir / f"slide-{number:02d}.png")
            output = temp / "contact-sheet.jpg"
            run([sys.executable, str(SCRIPTS / "make_contact_sheet.py"), "--input-dir", str(image_dir), "--output", str(output)])
            assert output.exists() and output.stat().st_size > 0

    print("all tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
