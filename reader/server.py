#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(__file__).resolve().parent / "static"
BOOKS_DIR = ROOT / "library" / "books"
NOTES_DIR = ROOT / "library" / "notes"
EXPORTS_DIR = ROOT / "library" / "exports"
ALLOWED_STATUS = {"unread", "reading", "done", "review"}


def read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def book_path(book_id: str) -> Path:
    return BOOKS_DIR / book_id / "book.json"


def notes_path(book_id: str) -> Path:
    return NOTES_DIR / f"{book_id}.json"


def load_book(book_id: str) -> dict:
    path = book_path(book_id)
    if not path.exists():
        raise FileNotFoundError(book_id)
    return read_json(path, {})


def load_notes(book_id: str) -> dict:
    return read_json(notes_path(book_id), {"book_id": book_id, "notes": {}})


def list_books() -> list[dict]:
    books = []
    for path in sorted(BOOKS_DIR.glob("*/book.json")):
        book = read_json(path, {})
        if not book:
            continue
        books.append(
            {
                "book_id": book.get("book_id"),
                "title": book.get("title"),
                "source": book.get("source", ""),
                "chapter_count": len(book.get("chapters", [])),
                "paragraph_count": len(book.get("paragraphs", [])),
            }
        )
    return books


def search_book(book_id: str, query: str) -> list[dict]:
    book = load_book(book_id)
    notes = load_notes(book_id).get("notes", {})
    q = query.strip().lower()
    if not q:
        return []

    chapter_titles = {c["id"]: c["title"] for c in book.get("chapters", [])}
    results = []
    for para in book.get("paragraphs", []):
        note = notes.get(para["id"], {})
        haystack_parts = [
            para.get("original", ""),
            para.get("plain_text", ""),
            para.get("reading_hint", ""),
            " ".join(para.get("notes", [])),
            note.get("my_note", ""),
            " ".join(note.get("tags", [])),
            note.get("status", ""),
        ]
        haystack = "\n".join(haystack_parts).lower()
        if q in haystack:
            results.append(
                {
                    "paragraph_id": para["id"],
                    "chapter_id": para["chapter_id"],
                    "chapter_title": chapter_titles.get(para["chapter_id"], ""),
                    "index": para["index"],
                    "original": para.get("original", ""),
                }
            )
    return results


def safe_export_name(title: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]+', "-", title).strip()
    return cleaned or "导出文稿"


def export_markdown(book_id: str) -> Path:
    book = load_book(book_id)
    notes_doc = load_notes(book_id)
    notes = notes_doc.get("notes", {})
    by_chapter = {}
    for para in book.get("paragraphs", []):
        by_chapter.setdefault(para["chapter_id"], []).append(para)

    lines = [
        f"# {book.get('title', book_id)}",
        "",
        f"来源：{book.get('source', '')}",
        "导出说明：本文件由本地阅读注释工具生成，合并底稿与个人笔记。",
        f"导出时间：{datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
    ]

    for chapter in book.get("chapters", []):
        lines.extend([f"## {chapter['title']}", ""])
        for para in by_chapter.get(chapter["id"], []):
            item = notes.get(para["id"], {})
            tags = item.get("tags", [])
            status = item.get("status", "unread")
            my_note = item.get("my_note", "").strip()
            lines.extend(
                [
                    f"### 第 {para['index']} 段",
                    "",
                    "**原文**",
                    "",
                ]
            )
            for line in para.get("original", "").splitlines():
                lines.append(f"> {line}")
            lines.extend(["", "**白话文**", "", para.get("plain_text", ""), "", "**注释**", ""])
            for note in para.get("notes", []):
                lines.append(f"- {note}")
            lines.extend(
                [
                    "",
                    "**理解提示**",
                    "",
                    para.get("reading_hint", ""),
                    "",
                    "**我的理解**",
                    "",
                    my_note or "> 在这里写你的理解、疑问或联想。",
                    "",
                    f"状态：{status}",
                    f"标签：{', '.join(tags) if tags else '无'}",
                    "",
                ]
            )

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORTS_DIR / f"{safe_export_name(book.get('title', book_id))}-阅读注释.md"
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        parsed = urlparse(path)
        rel = unquote(parsed.path.lstrip("/"))
        if not rel:
            rel = "index.html"
        resolved = (STATIC_DIR / rel).resolve()
        try:
            resolved.relative_to(STATIC_DIR.resolve())
        except ValueError:
            return str(STATIC_DIR / "__not_found__")
        return str(resolved)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_json(self, data, status: int = 200) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def send_error_json(self, message: str, status: int = 400) -> None:
        self.send_json({"error": message}, status)

    def read_body_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        try:
            if path == "/api/books":
                self.send_json({"books": list_books()})
                return
            match = re.fullmatch(r"/api/books/([^/]+)", path)
            if match:
                book_id = unquote(match.group(1))
                self.send_json({"book": load_book(book_id), "notes": load_notes(book_id)})
                return
            if path == "/api/search":
                qs = parse_qs(parsed.query)
                book_id = qs.get("book_id", [""])[0]
                query = qs.get("q", [""])[0]
                if not book_id:
                    self.send_error_json("missing book_id")
                    return
                self.send_json({"results": search_book(book_id, query)})
                return
        except FileNotFoundError:
            self.send_error_json("book not found", 404)
            return
        except Exception as exc:
            self.send_error_json(str(exc), 500)
            return
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        try:
            match = re.fullmatch(r"/api/books/([^/]+)/notes", path)
            if match:
                book_id = unquote(match.group(1))
                load_book(book_id)
                body = self.read_body_json()
                paragraph_id = body.get("paragraph_id", "").strip()
                if not paragraph_id:
                    self.send_error_json("missing paragraph_id")
                    return
                status = body.get("status") or "unread"
                if status not in ALLOWED_STATUS:
                    self.send_error_json("invalid status")
                    return
                tags = body.get("tags", [])
                if isinstance(tags, str):
                    tags = [t.strip() for t in re.split(r"[,，\\s]+", tags) if t.strip()]
                tags = [str(t).strip() for t in tags if str(t).strip()]

                notes_doc = load_notes(book_id)
                notes_doc.setdefault("notes", {})[paragraph_id] = {
                    "my_note": body.get("my_note", ""),
                    "tags": tags,
                    "status": status,
                    "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                }
                write_json(notes_path(book_id), notes_doc)
                self.send_json({"ok": True, "note": notes_doc["notes"][paragraph_id]})
                return
            match = re.fullmatch(r"/api/books/([^/]+)/export", path)
            if match:
                book_id = unquote(match.group(1))
                path = export_markdown(book_id)
                self.send_json({"ok": True, "path": str(path)})
                return
        except FileNotFoundError:
            self.send_error_json("book not found", 404)
            return
        except json.JSONDecodeError:
            self.send_error_json("invalid json")
            return
        except Exception as exc:
            self.send_error_json(str(exc), 500)
            return
        self.send_error_json("not found", 404)


def main() -> None:
    server = None
    port = 8000
    for candidate in range(8000, 8010):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", candidate), Handler)
            port = candidate
            break
        except OSError as exc:
            if exc.errno not in {48, 98, 10048}:
                raise
    if server is None:
        raise OSError("8000-8009 端口都不可用")
    print(f"阅读注释工具已启动：http://127.0.0.1:{port}")
    print("按 Ctrl+C 停止。")
    server.serve_forever()


if __name__ == "__main__":
    main()
