#!/usr/bin/env python3
"""Build the dependency-free Virae Logs static site."""

from __future__ import annotations

import argparse
import calendar
import html
import json
import re
import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "logs"
OUTPUT = ROOT / "_site"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ORDERED_RE = re.compile(r"^\s*\d+[.、]\s*(.+)$")
COMMIT_LINK_RE = re.compile(
    r"\[([0-9a-f]{7,8})\]\((https://github[.]com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/commit/[0-9a-f]{7,40})\)"
)
PROJECT_COMMIT_RE = re.compile(
    r"(?<=[（；])(?P<project>poly-terminal|polybot-dashboard|polybot|predictdog_docs|predictdog_skill|virae_ai_skill|prediction-bridge)"
    r"：(?P<references>[^；）]+)"
)
BARE_SHORT_HASH_RE = re.compile(r"(?<!\[)(?<![0-9a-f])([0-9a-f]{7,8})(?![0-9a-f])(?!\]\()")
PROJECT_GITHUB_REPOS = {
    "poly-terminal": "HQSV-Labs/poly-terminal",
    "polybot-dashboard": "HQSV-Labs/polybot-dashboard",
    "polybot": "HQSV-Labs/polybot",
    "predictdog_docs": "HQSV-Labs/predictdog_docs",
    "predictdog_skill": "HQSV-Labs/virae_ai_skill",
    "virae_ai_skill": "HQSV-Labs/virae_ai_skill",
    "prediction-bridge": "HQSV-Labs/prediction-bridge",
}


@dataclass(frozen=True)
class Report:
    day: str
    title: str
    lines: tuple[str, ...]

    @property
    def search_text(self) -> str:
        return " ".join((self.day, self.title, *self.lines))


def load_reports() -> list[Report]:
    reports: list[Report] = []
    for path in sorted(LOGS.glob("*.md"), reverse=True):
        if not DATE_RE.fullmatch(path.stem):
            raise ValueError(f"Invalid log filename: {path.name}")
        date.fromisoformat(path.stem)
        lines = path.read_text(encoding="utf-8").splitlines()
        if not lines or not lines[0].startswith("# "):
            raise ValueError(f"{path.name} must begin with a level-one heading")
        reports.append(Report(path.stem, lines[0][2:].strip(), tuple(lines[1:])))
    if len({report.day for report in reports}) != len(reports):
        raise ValueError("Duplicate report dates")
    return reports


def add_direct_commit_links(text: str) -> str:
    def link_project_references(match: re.Match[str]) -> str:
        project = match.group("project")
        github_repo = PROJECT_GITHUB_REPOS[project]
        references = BARE_SHORT_HASH_RE.sub(
            lambda hash_match: (
                f"[{hash_match.group(1)}]"
                f"(https://github.com/{github_repo}/commit/{hash_match.group(1)})"
            ),
            match.group("references"),
        )
        return f"{project}：{references}"

    return PROJECT_COMMIT_RE.sub(link_project_references, text)


def inline(text: str) -> str:
    text = add_direct_commit_links(text)
    chunks: list[str] = []
    cursor = 0
    for match in COMMIT_LINK_RE.finditer(text):
        chunks.append(html.escape(text[cursor:match.start()], quote=False))
        label = html.escape(match.group(1))
        url = html.escape(match.group(2), quote=True)
        chunks.append(f'<a href="{url}" rel="noreferrer">{label}</a>')
        cursor = match.end()
    chunks.append(html.escape(text[cursor:], quote=False))
    escaped = "".join(chunks)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)


def render_body(lines: tuple[str, ...]) -> str:
    chunks: list[str] = []
    in_list = False
    for raw in lines:
        line = raw.strip()
        if not line:
            # Markdown commonly separates ordered-list items with blank lines.
            # Keep the list open until a real block boundary appears.
            continue
        if line.startswith("## "):
            if in_list:
                chunks.append("</ol>")
                in_list = False
            chunks.append(f"<h2>{inline(line[3:])}</h2>")
            continue
        if line.startswith("【") and line.endswith("】"):
            if in_list:
                chunks.append("</ol>")
                in_list = False
            chunks.append(f"<h3>{inline(line[1:-1])}</h3>")
            continue
        match = ORDERED_RE.match(line)
        if match:
            if not in_list:
                chunks.append("<ol>")
                in_list = True
            chunks.append(f"<li>{inline(match.group(1))}</li>")
            continue
        if in_list:
            chunks.append("</ol>")
            in_list = False
        class_name = ' class="footer-note"' if line.startswith("——") else ""
        chunks.append(f"<p{class_name}>{inline(line)}</p>")
    if in_list:
        chunks.append("</ol>")
    return "\n".join(chunks)


def render_calendars(reports: list[Report]) -> str:
    report_days = {report.day for report in reports}
    months = sorted({report.day[:7] for report in reports}, reverse=True)
    month_names = ("一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月")
    month_views: list[str] = []
    for index, month in enumerate(months):
        year, month_number = map(int, month.split("-"))
        label = f"{year}年{month_names[month_number - 1]}"
        cells: list[str] = []
        for week in calendar.Calendar(firstweekday=0).monthdayscalendar(year, month_number):
            for day_number in week:
                if day_number == 0:
                    cells.append('<span class="calendar-day is-blank" aria-hidden="true"></span>')
                    continue
                day = f"{month}-{day_number:02d}"
                if day in report_days:
                    cells.append(
                        f'<a class="calendar-day has-log" href="#log-{day}" data-calendar-date="{day}" '
                        f'aria-label="查看 {day} 日志">{day_number}</a>'
                    )
                else:
                    cells.append(f'<span class="calendar-day is-empty" aria-label="{day} 无日志">{day_number}</span>')
        hidden = "" if index == 0 else " hidden"
        month_views.append(
            f'<div class="calendar-month" data-calendar-month="{month}" data-calendar-label="{label}"{hidden}>'
            f'<div class="calendar-grid">{"".join(cells)}</div></div>'
        )

    return f"""<section class="calendar" aria-labelledby="calendar-heading">
  <div class="section-heading"><h2 id="calendar-heading">日期导航</h2><span>{len(reports)} 天</span></div>
  <div class="calendar-toolbar">
    <button type="button" data-calendar-prev aria-label="上一个月">←</button>
    <strong data-calendar-title>{html.escape(month_views and f'{months[0][:4]}年{month_names[int(months[0][5:]) - 1]}' or '')}</strong>
    <button type="button" data-calendar-next aria-label="下一个月">→</button>
  </div>
  <div class="calendar-weekdays" aria-hidden="true"><span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span><span>日</span></div>
  {''.join(month_views)}
</section>"""


def page(title: str, body: str, *, description: str, depth: int = 0) -> str:
    prefix = "../" * depth
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{html.escape(description, quote=True)}">
  <meta name="theme-color" content="#fafafa">
  <title>{html.escape(title)}</title>
  <link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="{prefix}assets/styles.css">
</head>
<body>
<a class="skip-link" href="#main-content">跳到主要内容</a>
{body}
</body>
</html>
"""


def build(reports: list[Report]) -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir()
    shutil.copytree(ROOT / "assets", OUTPUT / "assets")
    (OUTPUT / ".nojekyll").write_text("", encoding="utf-8")

    cards = []
    for report in reports:
        cards.append(f"""<article class="report-card" id="log-{report.day}" data-report data-date="{report.day}" data-search-text="{html.escape(report.search_text, quote=True)}">
  <time class="report-date" datetime="{report.day}"><span>{report.day[:4]}</span>{report.day[5:]}</time>
  <div class="report-content">
    <h2 class="sr-only">{html.escape(report.day)} 更新</h2>
    {render_body(report.lines)}
    <a class="permalink" href="logs/{report.day}/">查看独立页面 →</a>
  </div>
</article>""")

        target = OUTPUT / "logs" / report.day
        target.mkdir(parents=True)
        detail_body = f"""<header class="site-header detail-header"><div class="shell">
  <a class="back" href="../../">← 返回全部日志</a>
  <p class="eyebrow">Virae.ai · Daily change log</p>
  </div></header>
<main class="shell detail" id="main-content"><h1>{html.escape(report.title)}</h1>{render_body(report.lines)}</main>
<footer class="site-footer"><div class="shell">从真实代码变动中提炼 · Asia/Shanghai</div></footer>"""
        (target / "index.html").write_text(
            page(report.title, detail_body, description=f"Virae.ai {report.day} 项目变动总结", depth=2),
            encoding="utf-8",
        )

    newest = reports[0].day if reports else "暂无"
    oldest = reports[-1].day if reports else "暂无"
    index_body = f"""<div class="app-shell">
<aside class="sidebar">
  <header class="site-header">
    <p class="eyebrow">Daily product change log</p>
    <h1 class="site-title">Virae Logs</h1>
    <p class="site-intro">把分散在前端、后端与 Bot 的代码变化，整理成使用者真正能感知的功能更新。</p>
    <div class="meta-row"><span><strong>{len(reports)}</strong> 篇日报</span><span>{oldest} — {newest}</span></div>
  </header>
  <div class="toolbar"><label class="sr-only" for="log-search">搜索更新日志</label><input id="log-search" class="search" type="search" data-search placeholder="搜索功能、项目或日期…"></div>
  {render_calendars(reports)}
  <p class="update-note">每日 22:00 CST 更新</p>
</aside>
<main class="content" id="main-content">
  <div class="content-heading"><h2>项目更新</h2></div>
  <section class="timeline" aria-label="更新日志">{''.join(cards)}</section>
  <p class="empty" data-empty hidden>没有找到匹配的日志。</p>
</main>
</div>
<footer class="site-footer"><div class="shell">Virae.ai 项目变动总结 · 由 Codex 自动整理</div></footer>
<script src="assets/app.js" defer></script>"""
    (OUTPUT / "index.html").write_text(
        page("Virae Logs", index_body, description="Virae.ai 每日产品与技术变动日志"),
        encoding="utf-8",
    )

    payload = [{"date": report.day, "title": report.title, "text": "\n".join(report.lines).strip()} for report in reports]
    (OUTPUT / "logs.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate and build the site")
    parser.parse_args()
    reports = load_reports()
    build(reports)
    print(f"Built {len(reports)} reports into {OUTPUT}")


if __name__ == "__main__":
    main()
