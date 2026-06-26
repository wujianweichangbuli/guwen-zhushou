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

## 文件结构

- `library/books/`：书籍底稿数据，包含原文、白话、注释和理解提示。
- `library/notes/`：你的个人理解、标签和阅读状态。
- `library/exports/`：导出的可读 Markdown。
- `reader/`：本地网页工具。
- `tools/`：导入或整理脚本。

个人注释以 `library/notes/` 为准；导出的 Markdown 是阅读和分享用的合并版本。

## 新增书籍

目前项目中已经导入：

- 《公孙龙子》
- 《鬼谷子》

之后新增 CText 或粘贴文本来源的书，可以继续让 Codex 生成 `library/books/<book_id>/book.json` 和对应的 `library/notes/<book_id>.json`，本地网页会自动出现在书籍列表中。
