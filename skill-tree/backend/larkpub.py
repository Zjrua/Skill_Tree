"""larkpub.py — 封装 lark-cli subprocess,发布飞书文档(wiki 归档优先)并返回 (url, kind)。"""
from __future__ import annotations
import os, sys
import re
import subprocess

URL_RE = re.compile(r"https?://\S+/(?:docx|wiki)/\S+")
DOCX_TOKEN_RE = re.compile(r"/docx/([A-Za-z0-9]+)")


def resolve_lark_cli() -> str:
    """优先用 SKILLTREE_BIN_DIR 下的 lark-cli(Tauri 解压位置);否则退 PATH 里的 lark-cli。"""
    bin_dir = os.environ.get("SKILLTREE_BIN_DIR")
    if bin_dir:
        exe = "lark-cli.exe" if sys.platform == "win32" else "lark-cli"
        local = os.path.join(bin_dir, exe)
        if os.path.exists(local):
            return local
    return "lark-cli"   # 退 PATH(开发期 / 用户自装)


def _run(cmd: list[str]) -> tuple[int, str, str]:
    """执行命令，返回 (returncode, stdout, stderr)。外部可被 monkeypatch。"""
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    return p.returncode, p.stdout, p.stderr


def parse_doc_url(output: str) -> str:
    m = URL_RE.search(output)
    return m.group(0).strip() if m else ""


def parse_docx_token(output: str) -> str:
    """从 docs +create 输出里提取 docx token(用于 wiki +move 的源 token)。"""
    m = DOCX_TOKEN_RE.search(output)
    return m.group(1) if m else ""


def publish_doc(xml_content: str, title: str = "学习笔记",
                wiki_space_id: str | None = None) -> tuple[str, str]:
    """发布文档。wiki_space_id 有 → docs+create 拿 token,再 wiki+move 归档到知识库;
    无 → 仅 docs+create。返回 (url, kind:"wiki"|"docx")。失败返回 ("", "")。"""
    # 1) 先 docs +create 拿 docx(无论是否归档 wiki,都需要这份文档)
    lark = resolve_lark_cli()
    create_cmd = [lark, "docs", "+create", "--as", "user", "--content", xml_content]
    try:
        code, out, err = _run(create_cmd)
    except Exception:
        return "", ""
    if code != 0:
        return "", ""
    docx_url = parse_doc_url(out)
    if not wiki_space_id:
        return docx_url, "docx"
    # 2) wiki +move 归档
    token = parse_docx_token(out)
    if not token:
        return docx_url, "docx"    # 拿不到 token,优雅降级为 docx
    move_cmd = [lark, "wiki", "+move", "--as", "user",
                "--obj-type", "docx", "--obj-token", token,
                "--target-space-id", wiki_space_id]
    try:
        mcode, mout, merr = _run(move_cmd)
    except Exception:
        return docx_url, "docx"    # move 失败,降级
    if mcode == 0:
        wiki_url = parse_doc_url(mout)
        if wiki_url:
            return wiki_url, "wiki"
    return docx_url, "docx"        # move 未产出 wiki url,降级
