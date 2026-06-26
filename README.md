# 古文阅读注释工具

这是一个本地阅读工具，用来管理多本古文的原文、白话、系统注释和个人理解。

## 启动

在本目录运行：

```bash
python3 reader/server.py
```

然后打开：

```text
http://127.0.0.1:8000
```

## 使用方式

- 左侧选择书籍和篇章。
- 中间阅读原文、白话文、注释和理解提示。
- 在“我的理解”里写自己的笔记。
- 用“标签”记录主题，例如：`名实`、`疑问`、`可复习`。
- 修改后点击“保存本段”。
- 点击“导出 Markdown”可生成合并文稿，文件会保存在 `library/exports/`。

## 在线同步

GitHub Pages 在线版会默认读取 `docs/data/notes/` 里的已发布注释。网页中继续修改后，注释会先保存在当前浏览器。

需要把当前书的注释上传回 GitHub 时，在网页的“GitHub 同步”区域填入有仓库 `Contents` 读写权限的 GitHub token，然后点击“上传注释”。上传会同时更新：

- `library/notes/<book_id>.json`
- `docs/data/notes/<book_id>.json`

GitHub Pages 刷新可能需要几十秒到几分钟。

## 文件结构

- `library/books/`：书籍底稿数据，包含原文、白话、注释和理解提示。
- `library/notes/`：你的个人理解、标签和阅读状态。
- `library/exports/`：导出的可读 Markdown。
- `reader/`：本地网页工具。
- `docs/`：GitHub Pages 在线版。
- `tools/`：导入或整理脚本。

个人注释以 `library/notes/` 为准；导出的 Markdown 是阅读和分享用的合并版本。

## 新增书籍

目前项目中已经导入：

- 《公孙龙子》
- 《鬼谷子》

之后新增 CText 或粘贴文本来源的书，可以继续让 Codex 生成 `library/books/<book_id>/book.json` 和对应的 `library/notes/<book_id>.json`，本地网页会自动出现在书籍列表中。
