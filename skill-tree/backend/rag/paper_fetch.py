"""rag/paper_fetch.py — 论文 abstract 抓取 + 本地缓存（零依赖 urllib）。"""
from __future__ import annotations
import json
import re
import time
import urllib.request

ARXIV_ABS = re.compile(r"arxiv\.org/abs/([0-9]{4}\.[0-9]+)")
ARXIV_PDF = re.compile(r"arxiv\.org/pdf/([0-9]{4}\.[0-9]+)")


def extract_arxiv_id(url: str) -> str | None:
    m = ARXIV_ABS.search(url) or ARXIV_PDF.search(url)
    return m.group(1) if m else None


def _fetch_url(url: str) -> str:
    """抓取 URL 文本。外部可被 monkeypatch 替换。"""
    req = urllib.request.Request(url, headers={"User-Agent": "skill-tree-agent/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _extract_abstract(html: str) -> str:
    """从 arxiv 页面粗提取 abstract 段。外部可被替换。"""
    m = re.search(r"<blockquote[^>]*class=\"abstract[^>]*>(.*?)</blockquote>", html, re.S | re.I)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    # 退路：找 Abstract: 之后一段
    m = re.search(r"Abstract:\s*(.{20,400})", html, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def fetch_abstract(url: str, cache_dir) -> dict:
    """抓论文 abstract，缓存到 cache_dir/<arxiv_id>.json。返回 {id, url, title?, abstract, fetched_at}。"""
    cache_dir = _path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    aid = extract_arxiv_id(url) or url.rsplit("/", 1)[-1]
    cache_file = cache_dir / f"{aid}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))
    try:
        html = _fetch_url(url)
    except Exception as e:
        return {"id": aid, "url": url, "abstract": "", "error": str(e),
                "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    title_m = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    title = re.sub(r"\s+", " ", title_m.group(1)).strip() if title_m else aid
    rec = {"id": aid, "url": url, "title": title, "abstract": _extract_abstract(html),
           "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    cache_file.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    return rec


def _path(p) -> "Path":
    from pathlib import Path
    return p if isinstance(p, Path) else Path(p)
