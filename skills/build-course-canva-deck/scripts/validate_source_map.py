#!/usr/bin/env python3
"""Validate a source map and record a user-declared outline mode."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def validate(payload: dict) -> list[str]:
    errors: list[str] = []
    if not payload.get("authoritative"):
        errors.append("authoritative source is not confirmed")
    if not payload.get("authoritative_source"):
        errors.append("authoritative_source is missing")
    nodes = payload.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        return errors + ["nodes must be a non-empty list"]
    ids: set[str] = set()
    orders: list[int] = []
    for index, node in enumerate(nodes, start=1):
        node_id = node.get("id")
        if not node_id or node_id in ids:
            errors.append(f"node {index} has a missing or duplicate id")
        ids.add(node_id)
        if not str(node.get("text", "")).strip():
            errors.append(f"node {node_id or index} has empty text")
        order = node.get("order")
        if not isinstance(order, int):
            errors.append(f"node {node_id or index} has invalid order")
        else:
            orders.append(order)
    if orders != list(range(1, len(nodes) + 1)):
        errors.append("node order must be contiguous and match list order")
    position = {node.get("id"): i for i, node in enumerate(nodes)}
    depth_by_id = {node.get("id"): node.get("depth") for node in nodes}
    for node in nodes:
        parent = node.get("parent_id")
        if parent is None:
            continue
        if parent not in ids:
            errors.append(f"node {node.get('id')} references missing parent {parent}")
        elif position[parent] >= position[node.get("id")]:
            errors.append(f"node {node.get('id')} appears before its parent {parent}")
        elif isinstance(depth_by_id.get(parent), int) and isinstance(node.get("depth"), int):
            if depth_by_id[parent] >= node["depth"]:
                errors.append(f"node {node.get('id')} depth must be greater than parent {parent}")
    mode = payload.get("outline_mode")
    if mode is not None and mode not in {"detailed", "sparse"}:
        errors.append("outline_mode must be detailed, sparse, or null")
    if mode and not payload.get("mode_declared_by_user"):
        errors.append("outline_mode exists without mode_declared_by_user=true")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_map", type=Path)
    parser.add_argument("--mode", choices=["detailed", "sparse"])
    parser.add_argument("--pdf-visual-check", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--require-mode", action="store_true")
    parser.add_argument("--require-pdf-visual-check", action="store_true")
    args = parser.parse_args()

    path = args.source_map.expanduser().resolve()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if args.mode:
        payload["outline_mode"] = args.mode
        payload["mode_declared_by_user"] = True
        payload["mode_declared_at"] = datetime.now(timezone.utc).isoformat()
        payload["requires_user_outline_mode"] = False
    if args.pdf_visual_check:
        payload["pdf_visual_hierarchy_verified"] = True
        payload["pdf_visual_hierarchy_verified_at"] = datetime.now(timezone.utc).isoformat()
        payload["pdf_visual_hierarchy_note"] = (
            "PDF pages were rendered and visually inspected for hierarchy, connectors, "
            "and unreadable regions before authoring."
        )
    errors = validate(payload)
    if args.require_mode and payload.get("outline_mode") not in {"detailed", "sparse"}:
        errors.append("user must explicitly choose 细纲 or 粗纲 before authoring")
    if (
        args.require_pdf_visual_check
        and str(payload.get("source_type", "")).lower() == "pdf"
        and payload.get("pdf_visual_hierarchy_verified") is not True
    ):
        errors.append("PDF source maps require rendered-page visual hierarchy verification before authoring")
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 1
    if args.write:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "mode": payload.get("outline_mode"), "nodes": len(payload["nodes"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
