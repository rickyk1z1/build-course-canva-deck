#!/usr/bin/env python3
"""Extract an ordered, format-neutral source map from a course outline file."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class SourceMapBuilder:
    def __init__(self, source: Path, source_type: str, assets_dir: Path):
        self.source = source
        self.source_type = source_type
        self.assets_dir = assets_dir
        self.nodes: list[dict[str, Any]] = []
        self.images: list[dict[str, Any]] = []
        self.warnings: list[str] = []
        self._image_sha_to_id: dict[str, str] = {}

    def add_node(
        self,
        text: str,
        *,
        parent_id: str | None,
        depth: int,
        kind: str,
        locator: str,
    ) -> str | None:
        text = clean(text)
        if not text:
            return None
        node_id = f"n{len(self.nodes) + 1:04d}"
        parent_node = next((node for node in self.nodes if node.get("id") == parent_id), None)
        parent_path_ids = list(parent_node.get("source_path_ids", [])) if parent_node else []
        parent_path_text = list(parent_node.get("source_path_text", [])) if parent_node else []
        source_path_ids = [*parent_path_ids, node_id]
        source_path_text = [*parent_path_text, text]
        self.nodes.append(
            {
                "id": node_id,
                "order": len(self.nodes) + 1,
                "parent_id": parent_id,
                "depth": max(depth, 0),
                "kind": kind,
                "text": text,
                "source_locator": locator,
                "source_path_ids": source_path_ids,
                "source_path_text": source_path_text,
                "source_path": " > ".join(source_path_text),
                "include": True,
            }
        )
        return node_id

    def add_image(
        self,
        path: Path,
        locator: str,
        *,
        source_node_id: str | None = None,
        source_node_text: str | None = None,
        source_path_ids: list[str] | None = None,
        source_path_text: list[str] | None = None,
    ) -> str | None:
        if not path.exists() or path.stat().st_size == 0:
            return None
        digest = sha256(path)
        existing_id = self._image_sha_to_id.get(digest)
        if existing_id:
            if source_node_id:
                for image in self.images:
                    if image.get("id") != existing_id:
                        continue
                    image.setdefault("source_node_ids", [])
                    if source_node_id not in image["source_node_ids"]:
                        image["source_node_ids"].append(source_node_id)
                    image.setdefault("source_node_texts", [])
                    if source_node_text and source_node_text not in image["source_node_texts"]:
                        image["source_node_texts"].append(source_node_text)
                    break
            return existing_id
        image_id = f"img{len(self.images) + 1:03d}"
        item = {
            "id": image_id,
            "path": str(path.resolve()),
            "source_locator": locator,
            "sha256": digest,
        }
        if source_node_id:
            item.update(
                {
                    "source_node_id": source_node_id,
                    "source_node_text": source_node_text or "",
                    "source_path_ids": source_path_ids or [],
                    "source_path_text": source_path_text or [],
                    "source_path": " > ".join(source_path_text or []),
                    "source_node_ids": [source_node_id],
                    "source_node_texts": [source_node_text or ""],
                }
            )
        self.images.append(item)
        self._image_sha_to_id[digest] = image_id
        return image_id

    def result(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "authoritative": True,
            "authoritative_source": str(self.source.resolve()),
            "source_type": self.source_type,
            "source_sha256": sha256(self.source),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "outline_mode": None,
            "mode_declared_by_user": False,
            "requires_user_outline_mode": True,
            "nodes": self.nodes,
            "images": self.images,
            "warnings": self.warnings,
        }


def parse_markdown_or_text(builder: SourceMapBuilder, text: str, markdown: bool) -> None:
    stack: list[tuple[int, str, str]] = []

    def current_heading_base() -> int:
        for depth, _, kind in reversed(stack):
            if kind == "heading":
                return depth
        return -1

    def add_at_depth(text_value: str, *, depth: int, kind: str, locator: str) -> None:
        while stack and stack[-1][0] >= depth:
            stack.pop()
        parent = stack[-1][1] if stack else None
        node = builder.add_node(
            text_value, parent_id=parent, depth=depth, kind=kind, locator=locator,
        )
        if node:
            stack.append((depth, node, kind))

    for line_number, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip():
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", raw) if markdown else None
        bullet = re.match(r"^(\s*)[-*+]\s+(.+)$", raw)
        numbered = re.match(r"^(\s*)\d+[.)、]\s*(.+)$", raw)
        if heading:
            level = len(heading.group(1))
            add_at_depth(
                heading.group(2), depth=level - 1,
                kind="heading", locator=f"line:{line_number}",
            )
            continue
        match = bullet or numbered
        if match:
            indent = len(match.group(1).replace("\t", "    ")) // 2
            base = current_heading_base()
            depth = base + 1 + indent if base >= 0 else indent
            add_at_depth(
                match.group(2), depth=depth,
                kind="list-item", locator=f"line:{line_number}",
            )
            continue
        indent = len(raw) - len(raw.lstrip(" \t"))
        base = current_heading_base()
        depth = base + 1 if base >= 0 else indent // 2
        add_at_depth(
            raw, depth=depth, kind="paragraph",
            locator=f"line:{line_number}",
        )


def parse_opml(builder: SourceMapBuilder, path: Path) -> None:
    root = ET.parse(path).getroot()

    def visit(element: ET.Element, parent: str | None, depth: int) -> None:
        text = element.attrib.get("text") or element.attrib.get("title") or ""
        current = builder.add_node(
            text, parent_id=parent, depth=depth, kind="topic",
            locator=f"outline:{len(builder.nodes) + 1}",
        )
        for child in element.findall("outline"):
            visit(child, current or parent, depth + 1)

    body = root.find("body")
    if body is None:
        raise ValueError("OPML body not found")
    for outline in body.findall("outline"):
        visit(outline, None, 0)


def parse_freemind(builder: SourceMapBuilder, path: Path) -> None:
    root = ET.parse(path).getroot()

    def visit(element: ET.Element, parent: str | None, depth: int) -> None:
        current = builder.add_node(
            element.attrib.get("TEXT", ""), parent_id=parent, depth=depth,
            kind="topic", locator=f"node:{element.attrib.get('ID', len(builder.nodes) + 1)}",
        )
        for child in element.findall("node"):
            visit(child, current or parent, depth + 1)

    for node in root.findall("node"):
        visit(node, None, 0)


def safe_archive_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", Path(name).name).strip("-") or "asset"


def archive_image_target(builder: SourceMapBuilder, archive: zipfile.ZipFile, name: str, used_names: set[str]) -> Path:
    filename = safe_archive_name(name)
    if filename in used_names:
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        filename = f"{len(used_names) + 1:03d}-{stem}{suffix}"
    used_names.add(filename)
    target = builder.assets_dir / filename
    if not target.exists():
        target.write_bytes(archive.read(name))
    return target


def extract_archive_images(builder: SourceMapBuilder, archive: zipfile.ZipFile, *, anchored_only: bool = False) -> dict[str, Path]:
    builder.assets_dir.mkdir(parents=True, exist_ok=True)
    allowed = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
    copied: dict[str, Path] = {}
    seen: set[str] = set()
    for name in archive.namelist():
        suffix = Path(name).suffix.lower()
        if suffix not in allowed or name.endswith("/"):
            continue
        target = archive_image_target(builder, archive, name, seen)
        copied[name] = target
        if not anchored_only:
            builder.add_image(target, f"archive:{name}")
    return copied


def parse_xmind(builder: SourceMapBuilder, path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        archive_images = extract_archive_images(builder, archive, anchored_only=True)
        anchored_archive_names: set[str] = set()
        if "content.json" in archive.namelist():
            payload = json.loads(archive.read("content.json"))

            def visit(topic: dict[str, Any], parent: str | None, depth: int, locator: str) -> None:
                current = builder.add_node(
                    topic.get("title", ""), parent_id=parent, depth=depth,
                    kind="topic", locator=locator,
                )
                image = topic.get("image") if isinstance(topic.get("image"), dict) else None
                image_src = str((image or {}).get("src") or "").strip()
                if image_src:
                    archive_name = image_src
                    if archive_name.startswith("xap:"):
                        archive_name = archive_name[4:]
                    archive_name = archive_name.lstrip("/")
                    target = archive_images.get(archive_name)
                    anchor_id = current or parent
                    anchor_node = next((node for node in builder.nodes if node.get("id") == anchor_id), None)
                    if target and anchor_node:
                        builder.add_image(
                            target,
                            f"{locator}:image:{archive_name}",
                            source_node_id=str(anchor_node.get("id")),
                            source_node_text=str(anchor_node.get("text", "")),
                            source_path_ids=list(anchor_node.get("source_path_ids", [])),
                            source_path_text=list(anchor_node.get("source_path_text", [])),
                        )
                        anchored_archive_names.add(archive_name)
                    elif target and not anchor_node:
                        builder.warnings.append(
                            f"image referenced by topic has no textual node anchor: {archive_name}"
                        )
                    else:
                        builder.warnings.append(
                            f"image referenced by topic was not found in archive: {archive_name}"
                        )
                notes = clean(((topic.get("notes") or {}).get("plain") or {}).get("content"))
                if notes:
                    builder.add_node(
                        notes, parent_id=current or parent, depth=depth + 1,
                        kind="note", locator=f"{locator}:notes",
                    )
                children = topic.get("children") or {}
                ordered: list[dict[str, Any]] = []
                for key in ("attached", "detached"):
                    value = children.get(key) or []
                    if isinstance(value, list):
                        ordered.extend(value)
                for index, child in enumerate(ordered, start=1):
                    visit(child, current or parent, depth + 1, f"{locator}.{index}")

            sheets = payload if isinstance(payload, list) else [payload]
            for sheet_index, sheet in enumerate(sheets, start=1):
                root_topic = sheet.get("rootTopic") or {}
                visit(root_topic, None, 0, f"sheet:{sheet_index}")
            for archive_name, target in archive_images.items():
                if archive_name in anchored_archive_names:
                    continue
                if "thumbnail" in archive_name.lower():
                    builder.add_image(target, f"archive:{archive_name}")
                elif Path(archive_name).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}:
                    builder.warnings.append(
                        f"image resource has no topic anchor and was not treated as a source case image: {archive_name}"
                    )
            return
        if "content.xml" not in archive.namelist():
            raise ValueError("XMind archive has neither content.json nor content.xml")
        xml_root = ET.fromstring(archive.read("content.xml"))

        def local(tag: str) -> str:
            return tag.rsplit("}", 1)[-1]

        def direct_title(element: ET.Element) -> str:
            for child in element:
                if local(child.tag) == "title":
                    return "".join(child.itertext())
            return ""

        def visit_xml(topic: ET.Element, parent: str | None, depth: int, locator: str) -> None:
            current = builder.add_node(
                direct_title(topic), parent_id=parent, depth=depth,
                kind="topic", locator=locator,
            )
            child_topics = [item for item in topic.iter() if item is not topic and local(item.tag) == "topic"]
            direct: list[ET.Element] = []
            for candidate in child_topics:
                ancestor_topic = None
                for possible in topic.iter():
                    if possible is candidate:
                        break
                    if local(possible.tag) == "topic" and candidate in list(possible.iter()):
                        ancestor_topic = possible
                if ancestor_topic is topic:
                    direct.append(candidate)
            for index, child in enumerate(direct, start=1):
                visit_xml(child, current or parent, depth + 1, f"{locator}.{index}")

        roots = [item for item in xml_root.iter() if local(item.tag) == "topic"]
        if roots:
            visit_xml(roots[0], None, 0, "sheet:1")


def parse_docx(builder: SourceMapBuilder, path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        if "word/document.xml" not in archive.namelist():
            raise ValueError("DOCX document.xml not found")
        extract_archive_images(builder, archive)
        root = ET.fromstring(archive.read("word/document.xml"))
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        stack: list[tuple[int, str]] = []
        for index, paragraph in enumerate(root.findall(".//w:body/w:p", ns), start=1):
            text = "".join(item.text or "" for item in paragraph.findall(".//w:t", ns))
            if not clean(text):
                continue
            style_element = paragraph.find("./w:pPr/w:pStyle", ns)
            style = ""
            if style_element is not None:
                style = style_element.attrib.get(f"{{{ns['w']}}}val", "")
            heading_match = re.search(r"(?:Heading|标题)\s*([1-6])", style, re.I)
            if heading_match:
                level = int(heading_match.group(1))
                while stack and stack[-1][0] >= level:
                    stack.pop()
                parent = stack[-1][1] if stack else None
                node = builder.add_node(
                    text, parent_id=parent, depth=level - 1, kind="heading",
                    locator=f"paragraph:{index}",
                )
                if node:
                    stack.append((level, node))
            else:
                parent = stack[-1][1] if stack else None
                builder.add_node(
                    text, parent_id=parent, depth=len(stack), kind="paragraph",
                    locator=f"paragraph:{index}",
                )


def parse_pdf(builder: SourceMapBuilder, path: Path) -> None:
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(path))
        for page_number, page in enumerate(reader.pages, start=1):
            page_node = builder.add_node(
                f"Page {page_number}", parent_id=None, depth=0, kind="page",
                locator=f"page:{page_number}",
            )
            text = page.extract_text() or ""
            for line_number, line in enumerate(text.splitlines(), start=1):
                builder.add_node(
                    line, parent_id=page_node, depth=1, kind="text-line",
                    locator=f"page:{page_number}:line:{line_number}",
                )
            try:
                images = list(page.images)
            except Exception:
                images = []
            for image_index, image in enumerate(images, start=1):
                builder.assets_dir.mkdir(parents=True, exist_ok=True)
                name = safe_archive_name(getattr(image, "name", f"page-{page_number}-{image_index}.png"))
                target = builder.assets_dir / f"page-{page_number:03d}-{image_index:02d}-{name}"
                target.write_bytes(image.data)
                builder.add_image(target, f"page:{page_number}:image:{image_index}")
    except ImportError:
        pdftotext = shutil.which("pdftotext")
        if not pdftotext:
            raise RuntimeError("PDF extraction requires pypdf or pdftotext")
        process = subprocess.run(
            [pdftotext, "-layout", str(path), "-"], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        parse_markdown_or_text(builder, process.stdout, markdown=False)
    builder.warnings.append(
        "PDF text order is not accepted as mind-map hierarchy. Render and visually verify connectors and node levels."
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--assets-dir", type=Path)
    args = parser.parse_args()

    source = args.input.expanduser().resolve()
    if not source.is_file():
        parser.error(f"Input file does not exist: {source}")
    output = args.output.expanduser().resolve()
    assets_dir = (args.assets_dir or output.parent / "assets" / "source").expanduser().resolve()
    suffix = source.suffix.lower()
    source_type = suffix.lstrip(".") or "text"
    builder = SourceMapBuilder(source, source_type, assets_dir)

    if suffix == ".xmind":
        parse_xmind(builder, source)
    elif suffix == ".opml":
        parse_opml(builder, source)
    elif suffix == ".mm":
        parse_freemind(builder, source)
    elif suffix == ".docx":
        parse_docx(builder, source)
    elif suffix == ".pdf":
        parse_pdf(builder, source)
    elif suffix in {".md", ".markdown"}:
        parse_markdown_or_text(builder, source.read_text(encoding="utf-8"), markdown=True)
    elif suffix in {".txt", ""}:
        parse_markdown_or_text(builder, source.read_text(encoding="utf-8"), markdown=False)
    else:
        parser.error(f"Unsupported source type: {suffix or '(none)'}")

    if not builder.nodes:
        raise RuntimeError("No source nodes were extracted")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(builder.result(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "nodes": len(builder.nodes), "images": len(builder.images)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
