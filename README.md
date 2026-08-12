# Virae Logs

Virae.ai 的公开产品更新日志。每天 22:00（Asia/Shanghai）从实际 Git diff 中提炼使用者可感知的功能变化。

## 本地预览

```bash
python3 scripts/build.py
python3 -m http.server 8000 --directory _site
```

打开 <http://localhost:8000>。

## 新增日报

在 `logs/` 下新增 `YYYY-MM-DD.md`，第一行使用一级标题，正文使用普通段落、二级标题或有序列表。然后运行：

```bash
python3 scripts/build.py --check
```

提交到 `main` 后，GitHub Actions 会自动构建并部署 GitHub Pages。

## 内容原则

- 只统计 author name 为 `smallyunet` 的提交。
- 每个被引用的 commit 都检查实际 `git show` diff。
- 按完整功能点和用户场景合并，避免按仓库或 commit 流水账。
- 远端可确认的提交可以使用链接；未推送提交标注“仅本地”。

