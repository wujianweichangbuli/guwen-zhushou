const state = {
  books: [],
  book: null,
  notes: {},
  activeBookId: null,
  activeChapterId: null,
};

const $ = (id) => document.getElementById(id);

function showMessage(text, isError = false) {
  const el = $("message");
  el.textContent = text;
  el.classList.toggle("error", isError);
  el.hidden = !text;
  if (text && !isError) {
    window.clearTimeout(showMessage.timer);
    showMessage.timer = window.setTimeout(() => {
      el.hidden = true;
    }, 2600);
  }
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "请求失败");
  }
  return data;
}

async function loadBooks() {
  const data = await api("/api/books");
  state.books = data.books;
  renderBookList();
  if (state.books.length) {
    await loadBook(state.books[0].book_id);
  } else {
    $("bookTitle").textContent = "还没有书籍";
    $("paragraphs").innerHTML = "";
  }
}

async function loadBook(bookId) {
  const data = await api(`/api/books/${encodeURIComponent(bookId)}`);
  state.activeBookId = bookId;
  state.book = data.book;
  state.notes = data.notes.notes || {};
  state.activeChapterId = state.book.chapters[0]?.id || null;
  $("searchInput").value = "";
  $("searchResults").hidden = true;
  renderBookList();
  renderChapterList();
  renderBook();
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

async function saveParagraph(paragraphId) {
  const noteEl = document.querySelector(`[data-note="${cssEscape(paragraphId)}"]`);
  const tagsEl = document.querySelector(`[data-tags="${cssEscape(paragraphId)}"]`);
  const statusEl = document.querySelector(`[data-status="${cssEscape(paragraphId)}"]`);
  const saveState = document.querySelector(`[data-save-state="${cssEscape(paragraphId)}"]`);
  const payload = {
    paragraph_id: paragraphId,
    my_note: noteEl.value,
    tags: splitTags(tagsEl.value),
    status: statusEl.value,
  };
  saveState.textContent = "保存中...";
  try {
    const data = await api(`/api/books/${encodeURIComponent(state.activeBookId)}/notes`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    state.notes[paragraphId] = data.note;
    saveState.textContent = `已保存：${data.note.updated_at}`;
  } catch (error) {
    saveState.textContent = "保存失败";
    showMessage(error.message, true);
  }
}

function splitTags(value) {
  return value
    .split(/[，,\s]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

async function runSearch() {
  const q = $("searchInput").value.trim();
  const box = $("searchResults");
  if (!q || !state.activeBookId) {
    box.hidden = true;
    box.innerHTML = "";
    return;
  }
  const data = await api(`/api/search?book_id=${encodeURIComponent(state.activeBookId)}&q=${encodeURIComponent(q)}`);
  if (!data.results.length) {
    box.hidden = false;
    box.innerHTML = "没有找到匹配段落。";
    return;
  }
  box.hidden = false;
  box.innerHTML = data.results
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

async function exportBook() {
  if (!state.activeBookId) return;
  try {
    const data = await api(`/api/books/${encodeURIComponent(state.activeBookId)}/export`, { method: "POST" });
    showMessage(`已导出：${data.path}`);
  } catch (error) {
    showMessage(error.message, true);
  }
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
  searchTimer = window.setTimeout(() => runSearch().catch((error) => showMessage(error.message, true)), 180);
});
$("exportButton").addEventListener("click", exportBook);

loadBooks().catch((error) => showMessage(error.message, true));
