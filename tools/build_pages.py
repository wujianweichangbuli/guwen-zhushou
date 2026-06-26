#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOKS_DIR = ROOT / "library" / "books"
DOCS_DIR = ROOT / "docs"
DATA_DIR = DOCS_DIR / "data"


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / ".nojekyll").write_text("", encoding="utf-8")

    books = []
    for book_path in sorted(BOOKS_DIR.glob("*/book.json")):
        book = json.loads(book_path.read_text(encoding="utf-8"))
        book_id = book["book_id"]
        target = DATA_DIR / f"{book_id}.json"
        target.write_text(json.dumps(book, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        books.append(
            {
                "book_id": book_id,
                "title": book["title"],
                "source": book.get("source", ""),
                "chapter_count": len(book.get("chapters", [])),
                "paragraph_count": len(book.get("paragraphs", [])),
            }
        )

    (DATA_DIR / "books.json").write_text(
        json.dumps({"books": books}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    shutil.copyfile(ROOT / "reader" / "static" / "styles.css", DOCS_DIR / "styles.css")
    print(f"已生成 GitHub Pages 静态站点：{DOCS_DIR}")
    for book in books:
        print(f"- {book['title']}: {book['chapter_count']} 篇，{book['paragraph_count']} 段")


if __name__ == "__main__":
    main()
