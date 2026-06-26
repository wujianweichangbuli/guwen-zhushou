#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANNOTATION_DIR = ROOT / "公孙龙子白话注释"
BOOK_DIR = ROOT / "library" / "books" / "gongsunlongzi"
NOTES_PATH = ROOT / "library" / "notes" / "gongsunlongzi.json"

FILES = [
    ("ch01", "01-迹府.md"),
    ("ch02", "02-白马论.md"),
    ("ch03", "03-指物论.md"),
    ("ch04", "04-通变论.md"),
    ("ch05", "05-坚白论.md"),
    ("ch06", "06-名实论.md"),
]


def section(text: str, start: str, end: str | None = None) -> str:
    start_token = f"**{start}**"
    start_index = text.index(start_token) + len(start_token)
    if end is None:
        return text[start_index:].strip()
    end_token = f"**{end}**"
    return text[start_index : text.index(end_token, start_index)].strip()


def parse_chapter(chapter_id: str, path: Path) -> tuple[dict, list[dict]]:
    text = path.read_text(encoding="utf-8")
    title = re.search(r"^# (.+)$", text, flags=re.M).group(1)
    source = re.search(r"^来源：(.+)$", text, flags=re.M).group(1)
    parts = re.split(r"^### 第 (\d+) 段\s*$", text, flags=re.M)
    paragraphs = []
    for i in range(1, len(parts), 2):
        index = int(parts[i])
        block = parts[i + 1]
        original = "\n".join(
            line[2:] if line.startswith("> ") else line
            for line in section(block, "原文", "白话文").splitlines()
        ).strip()
        plain_text = section(block, "白话文", "注释")
        notes_block = section(block, "注释", "理解提示")
        notes = [
            line[2:].strip()
            for line in notes_block.splitlines()
            if line.strip().startswith("- ")
        ]
        reading_hint = section(block, "理解提示", "我的理解")
        paragraphs.append(
            {
                "id": f"gongsunlongzi-{chapter_id}-p{index:03d}",
                "chapter_id": chapter_id,
                "index": index,
                "original": original,
                "plain_text": plain_text,
                "notes": notes,
                "reading_hint": reading_hint,
            }
        )
    return {"id": chapter_id, "title": title, "source": source}, paragraphs


def main() -> None:
    chapters = []
    paragraphs = []
    source = ""
    for chapter_id, filename in FILES:
        chapter, items = parse_chapter(chapter_id, ANNOTATION_DIR / filename)
        if not source:
            source = chapter["source"]
        chapters.append({"id": chapter["id"], "title": chapter["title"]})
        paragraphs.extend(items)

    book = {
        "book_id": "gongsunlongzi",
        "title": "公孙龙子",
        "source": "https://ctext.org/gongsunlongzi/zhs",
        "chapters": chapters,
        "paragraphs": paragraphs,
    }

    BOOK_DIR.mkdir(parents=True, exist_ok=True)
    BOOK_DIR.joinpath("book.json").write_text(
        json.dumps(book, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if not NOTES_PATH.exists():
        NOTES_PATH.parent.mkdir(parents=True, exist_ok=True)
        NOTES_PATH.write_text(
            json.dumps({"book_id": "gongsunlongzi", "notes": {}}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(f"已导入《公孙龙子》：{len(chapters)} 篇，{len(paragraphs)} 段")


if __name__ == "__main__":
    main()
