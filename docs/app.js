const state = {
  books: [],
  book: null,
  notes: {},
  activeBookId: null,
  activeChapterId: null,
};

const $ = (id) => document.getElementById(id);

function storageKey(bookId) {
  return `guwen-notes:${bookId}`;
}

function showMessage(text, isError = false) {
  const el = $("message");
  el.textContent = text;
  el.classList.toggle("error", isError);
  el.hidden = !text;
  if (text && !isError) {
    window.clearTimeout(showMessage.timer);
    showMessage.timer = window.setTimeout(() => {
      el.hidden = true;
    }, 3000);
  }
}

async function loadJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`无法读取 ${path}`);
  }
  return response.json();
}

async function loadBooks() {
  const data = await loadJson("./data/books.json");
  state.books = data.books || [];
  renderBookList();
  if (state.books.length) {
    await loadBook(state.books[0].book_id);
  } else {
    $("bookTitle").textContent = "还没有书籍";
    $("paragraphs").innerHTML = "";
  }
}

async function loadBook(bookId) {
  const book = await loadJson(`./data/${encodeURIComponent(bookId)}.json`);
  state.activeBookId = bookId;
  state.book = book;
  state.notes = loadLocalNotes(bookId);
  state.activeChapterId = state.book.chapters[0]?.id || null;
  $("searchInput").value = "";
  $("searchResults").hidden = true;
  renderBookList();
  renderChapterList();
  renderBook();
}

function loadLocalNotes(bookId) {
  try {
    return JSON.parse(localStorage.getItem(storageKey(bookId)) || "{}");
  } catch {
    return {};
  }
}

function saveLocalNotes() {
  localStorage.setItem(storageKey(state.activeBookId), JSON.stringify(state.notes));
}

function renderBookList() {
  $("bookList").innerHTML = state.books
    .map(
      (book) => `
        <button class="book-item ${book.book_id === state.activeBookId ? "active" : ""}" data-book="${escapeHtml(book.book_id)}">
          <strong>${escapeHtml(book.title)}</strong><br>
          <span>${book.chapter_count} 篇 · ${book.paragraph_count} 段</span>
        </button>
      `
    )
    .join("");
  document.querySelectorAll("[data-book]").forEach((button) => {
    button.addEventListener("click", () => loadBook(button.dataset.book));
  });
}

function renderChapterList() {
  const chapters = state.book?.chapters || [];
  $("chapterList").innerHTML = chapters
    .map(
      (chapter) => `
        <button class="chapter-item ${chapter.id === state.activeChapterId ? "active" : ""}" data-chapter="${escapeHtml(chapter.id)}">
          ${escapeHtml(chapter.title)}
        </button>
      `
    )
    .join("");
  document.querySelectorAll("[data-chapter]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeChapterId = button.dataset.chapter;
      renderChapterList();
      renderBook();
      document.querySelector(".chapter-heading")?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
}

function renderBook() {
  const book = state.book;
  if (!book) return;

  $("bookTitle").textContent = book.title;
  $("bookMeta").textContent = `${book.chapters.length} 篇 · ${book.paragraphs.length} 段 · ${book.source || "无来源"}`;

  const chapter = book.chapters.find((item) => item.id === state.activeChapterId) || book.chapters[0];
  const paragraphs = book.paragraphs.filter((para) => para.chapter_id === chapter.id);
  $("paragraphs").innerHTML = `
    <h2 class="chapter-heading">${escapeHtml(chapter.title)}</h2>
    ${paragraphs.map(renderParagraph).join("")}
  `;

  bindParagraphEditors();
}

function renderParagraph(para) {
  const note = state.notes[para.id] || {};
  const tags = note.tags || [];
  return `
    <article class="para-card" id="${escapeHtml(para.id)}">
      <div class="para-head">
        <div class="para-title">第 ${para.index} 段</div>
        <select class="status" data-status="${escapeHtml(para.id)}">
          ${statusOption("unread", "未读", note.status)}
          ${statusOption("reading", "在读", note.status)}
          ${statusOption("done", "已读", note.status)}
          ${statusOption("review", "复习", note.status)}
        </select>
      </div>

      <div class="label">原文</div>
      <blockquote class="original">${escapeHtml(para.original)}</blockquote>

      <div class="label">白话文</div>
      <p class="plain">${escapeHtml(para.plain_text)}</p>

      <div class="label">注释</div>
      <ul class="system-notes">${(para.notes || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>

      <div class="label">理解提示</div>
      <p class="hint">${escapeHtml(para.reading_hint)}</p>

      <div class="label">我的理解</div>
      <textarea class="note-editor" data-note="${escapeHtml(para.id)}" placeholder="在这里写你的理解、疑问或联想。">${escapeHtml(note.my_note || "")}</textarea>

      <div class="label">标签</div>
      <input class="tags-input" data-tags="${escapeHtml(para.id)}" value="${escapeHtml(tags.join("，"))}" placeholder="例如：名实，疑问，可复习">

      <div class="save-row">
        <span class="save-state" data-save-state="${escapeHtml(para.id)}">${note.updated_at ? `上次保存：${escapeHtml(note.updated_at)}` : "尚未保存个人注释"}</span>
        <button type="button" data-save="${escapeHtml(para.id)}">保存本段</button>
      </div>
    </article>
  `;
}

function statusOption(value, label, current) {
  const selected = (current || "unread") === value ? "selected" : "";
  return `<option value="${value}" ${selected}>${label}</option>`;
}

function bindParagraphEditors() {
  document.querySelectorAll("[data-save]").forEach((button) => {
    button.addEventListener("click", () => saveParagraph(button.dataset.save));
  });
  document.querySelectorAll("[data-status]").forEach((select) => {
    select.addEventListener("change", () => saveParagraph(select.dataset.status));
  });
}

function saveParagraph(paragraphId) {
  const noteEl = document.querySelector(`[data-note="${cssEscape(paragraphId)}"]`);
  const tagsEl = document.querySelector(`[data-tags="${cssEscape(paragraphId)}"]`);
  const statusEl = document.querySelector(`[data-status="${cssEscape(paragraphId)}"]`);
  const saveState = document.querySelector(`[data-save-state="${cssEscape(paragraphId)}"]`);
  state.notes[paragraphId] = {
    my_note: noteEl.value,
    tags: splitTags(tagsEl.value),
    status: statusEl.value,
    updated_at: new Date().toISOString(),
  };
  saveLocalNotes();
  saveState.textContent = `已保存到当前浏览器：${state.notes[paragraphId].updated_at}`;
}

function splitTags(value) {
  return value
    .split(/[，,\s]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function searchBook(query) {
  const q = query.trim().toLowerCase();
  if (!q || !state.book) return [];
  const chapterTitles = Object.fromEntries(state.book.chapters.map((chapter) => [chapter.id, chapter.title]));
  return state.book.paragraphs
    .filter((para) => {
      const note = state.notes[para.id] || {};
      const haystack = [
        para.original,
        para.plain_text,
        para.reading_hint,
        (para.notes || []).join(" "),
        note.my_note || "",
        (note.tags || []).join(" "),
        note.status || "",
      ]
        .join("\n")
        .toLowerCase();
      return haystack.includes(q);
    })
    .map((para) => ({
      paragraph_id: para.id,
      chapter_id: para.chapter_id,
      chapter_title: chapterTitles[para.chapter_id] || "",
      index: para.index,
      original: para.original,
    }));
}

function runSearch() {
  const q = $("searchInput").value.trim();
  const box = $("searchResults");
  if (!q || !state.activeBookId) {
    box.hidden = true;
    box.innerHTML = "";
    return;
  }
  const results = searchBook(q);
  if (!results.length) {
    box.hidden = false;
    box.innerHTML = "没有找到匹配段落。";
    return;
  }
  box.hidden = false;
  box.innerHTML = results
    .slice(0, 80)
    .map(
      (item) => `
        <button class="search-result" data-result="${escapeHtml(item.paragraph_id)}" data-result-chapter="${escapeHtml(item.chapter_id)}">
          <strong>${escapeHtml(item.chapter_title)} · 第 ${item.index} 段</strong><br>
          <span>${escapeHtml(item.original.slice(0, 90))}${item.original.length > 90 ? "..." : ""}</span>
        </button>
      `
    )
    .join("");
  document.querySelectorAll("[data-result]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeChapterId = button.dataset.resultChapter;
      renderChapterList();
      renderBook();
      const target = document.getElementById(button.dataset.result);
      target?.classList.add("highlight");
      target?.scrollIntoView({ behavior: "smooth", block: "center" });
      setTimeout(() => target?.classList.remove("highlight"), 2200);
    });
  });
}

function exportBook() {
  if (!state.book) return;
  const chapterMap = Object.fromEntries(state.book.chapters.map((chapter) => [chapter.id, chapter]));
  const lines = [
    `# ${state.book.title}`,
    "",
    `来源：${state.book.source || ""}`,
    "导出说明：本文件由 GitHub Pages 在线版生成，合并底稿与当前浏览器中的个人笔记。",
    `导出时间：${new Date().toISOString()}`,
    "",
  ];

  for (const chapter of state.book.chapters) {
    lines.push(`## ${chapter.title}`, "");
    for (const para of state.book.paragraphs.filter((item) => item.chapter_id === chapter.id)) {
      const note = state.notes[para.id] || {};
      lines.push(`### 第 ${para.index} 段`, "", "**原文**", "");
      for (const line of para.original.split("\n")) lines.push(`> ${line}`);
      lines.push("", "**白话文**", "", para.plain_text, "", "**注释**", "");
      for (const item of para.notes || []) lines.push(`- ${item}`);
      lines.push("", "**理解提示**", "", para.reading_hint, "", "**我的理解**", "", note.my_note || "> 在这里写你的理解、疑问或联想。", "");
      lines.push(`状态：${note.status || "unread"}`, `标签：${(note.tags || []).join(", ") || "无"}`, "");
    }
  }
  downloadText(`${state.book.title}-阅读注释.md`, lines.join("\n").trim() + "\n");
}

function downloadText(filename, content) {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function cssEscape(value) {
  if (window.CSS && CSS.escape) return CSS.escape(value);
  return String(value).replace(/"/g, '\\"');
}

let searchTimer = null;
$("searchInput").addEventListener("input", () => {
  window.clearTimeout(searchTimer);
  searchTimer = window.setTimeout(runSearch, 180);
});
$("exportButton").addEventListener("click", exportBook);

loadBooks().catch((error) => showMessage(error.message, true));
