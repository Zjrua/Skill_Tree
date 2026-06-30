# tests/test_paper_fetch.py
from __future__ import annotations
from pathlib import Path

from rag.paper_fetch import extract_arxiv_id, fetch_abstract


def test_extract_arxiv_id_abs():
    assert extract_arxiv_id("https://arxiv.org/abs/1703.04247") == "1703.04247"


def test_extract_arxiv_id_pdf():
    assert extract_arxiv_id("https://arxiv.org/pdf/2402.17152.pdf") == "2402.17152"


def test_extract_arxiv_id_none():
    assert extract_arxiv_id("https://example.com/foo") is None


def test_fetch_abstract_caches(tmp_path: Path, monkeypatch):
    cache = tmp_path / "paper_cache"
    calls = {"n": 0}

    def fake_urlfetch(url: str) -> str:
        calls["n"] += 1
        return "<title>(PDF) DeepFM</title>Abstract: We propose DeepFM."

    monkeypatch.setattr("rag.paper_fetch._fetch_url", fake_urlfetch)
    monkeypatch.setattr("rag.paper_fetch._extract_abstract",
                        lambda html: "We propose DeepFM")

    r1 = fetch_abstract("https://arxiv.org/abs/1703.04247", cache)
    r2 = fetch_abstract("https://arxiv.org/abs/1703.04247", cache)
    assert calls["n"] == 1  # 第二次走缓存
    assert r1["abstract"] == "We propose DeepFM"
    assert r1["id"] == "1703.04247"
    assert (cache / "1703.04247.json").exists()
