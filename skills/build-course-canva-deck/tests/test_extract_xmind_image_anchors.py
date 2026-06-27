#!/usr/bin/env python3
"""Regression test: XMind source images keep their outline-node teaching anchor."""

from __future__ import annotations

import json
import subprocess
import tempfile
import zipfile
from pathlib import Path

EXTRACT = Path(__file__).resolve().parents[1] / "scripts" / "extract_source.py"


def write_minimal_xmind(path: Path) -> None:
    payload = [
        {
            "rootTopic": {
                "title": "Root",
                "children": {
                    "attached": [
                        {
                            "title": "Parent concept",
                            "children": {
                                "attached": [
                                    {
                                        "title": "",
                                        "image": {"src": "xap:resources/case.png"},
                                    }
                                ]
                            },
                        }
                    ]
                },
            }
        }
    ]
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("content.json", json.dumps(payload, ensure_ascii=False))
        archive.writestr("resources/case.png", b"fake-png-bytes")
        archive.writestr("Thumbnails/thumbnail.png", b"fake-thumbnail")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "course.xmind"
        output = root / "source-map.json"
        assets = root / "assets"
        write_minimal_xmind(source)

        result = subprocess.run(
            [
                "python3",
                str(EXTRACT),
                "--input",
                str(source),
                "--output",
                str(output),
                "--assets-dir",
                str(assets),
            ],
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr or result.stdout)

        data = json.loads(output.read_text(encoding="utf-8"))
        case_images = [
            image
            for image in data["images"]
            if "thumbnail" not in str(image.get("path", "")).lower()
        ]
        if len(case_images) != 1:
            raise AssertionError(data["images"])
        image = case_images[0]
        if image.get("source_node_text") != "Parent concept":
            raise AssertionError(image)
        if image.get("source_path_text") != ["Root", "Parent concept"]:
            raise AssertionError(image)
        if data.get("warnings"):
            raise AssertionError(data["warnings"])
    print("xmind image anchor extraction regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
