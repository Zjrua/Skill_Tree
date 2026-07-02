"""agent/tool_runtime.py — 工具执行器。

签名统一：execute_tool(name, args, ctx) -> str（给模型看的文本）。
写操作（add_node/add_tasks）只生成"建议"，由前端卡片确认后调 apply 端点真正写入。
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Any


class ToolError(Exception):
    pass


class ToolResult(dict):
    """工具执行结果。text=给模型看的文本;events=要 emit 的 SSE 事件(list[dict])。"""
    pass


def _ok(text: str, events: list | None = None) -> ToolResult:
    return ToolResult(text=text, events=events or [])


@dataclass
class Context:
    uid: str
    graph: dict                      # layout 计算后的图（nodes/overview）
    resume: dict | None              # 简历素材
    retriever: Any                   # rag.retriever.Retriever 实例（或 None）
    rag_index_dir: Any               # Path（论文缓存用）
    trees: list = None               # 原始树数据（含 branches，供 get_direction 用）# type: ignore
    cfg: dict | None = None          # 新:LLM 配置(add_node/add_tasks 生成节点用)


def execute_tool(name: str, args: dict, ctx: Context) -> ToolResult:
    fn = _REGISTRY.get(name)
    if not fn:
        raise ToolError(f"未知工具: {name}")
    return fn(args, ctx)


# ── 图谱工具 ──
def _get_progress(args, ctx):
    g = ctx.graph
    ov = g.get("overview", {})
    nodes = g.get("nodes", [])
    learning = [n for n in nodes if n.get("state") == "learning"]
    done = [n for n in nodes if n.get("state") == "done"]
    parts = [f"整体掌握度 {ov.get('overall_pct',0)}%，已掌握知识点 {ov.get('mastered_points',0)}/{ov.get('total_points',0)}。"]
    if learning:
        parts.append("进行中：" + "、".join(f"{n.get('name')}({n.get('pct',0)}%)" for n in learning[:8]))
    if done:
        parts.append("已点亮：" + "、".join(n.get("name", n.get("id")) for n in done[:8]))
    return _ok(" ".join(parts))


def _get_node(args, ctx):
    nid = args.get("node_id", "")
    for n in ctx.graph.get("nodes", []):
        if n.get("id") == nid:
            tasks = n.get("tasks", [])
            return _ok(f"节点 {n.get('name')}（{n.get('category','')}）"
                       f"，状态 {n.get('state')}，{n.get('pct',0)}%。"
                       f"任务：{json.dumps([t.get('title') for t in tasks], ensure_ascii=False)}"
                       f"。前置：{n.get('depends_on', [])}")
    return _ok(f"未找到节点 {nid}。")


def _get_next(args, ctx):
    nid = args.get("node_id", "")
    nodes = ctx.graph.get("nodes", [])
    # 反向依赖：谁 depends_on 了 nid
    children = [n.get("name", n.get("id")) for n in nodes if nid in (n.get("depends_on") or [])]
    if children:
        return _ok(f"{nid} 学完后建议：{'、'.join(children)}")
    return _ok(f"{nid} 暂无明确下游节点，可考虑补充。")


def _get_direction(args, ctx):
    """查某方向所有节点 + 进度 + 下一步建议。dir_id 支持模糊匹配 id/title。"""
    did = (args.get("dir_id") or "").lower()
    trees = ctx.trees or []
    target = None
    for t in trees:
        if did in (t.get("tree_id", "").lower()) or did in t.get("title", "").lower():
            target = t
            break
    if not target:
        return _ok(f"未找到方向 {did}。")
    import progress as _P
    lines = [f"方向：{target.get('title')} {target.get('icon','')}"]
    nodes = []
    for b in target.get("branches", []):
        for n in b.get("nodes", []):
            m, tot, pct = _P.node_mastery(n)
            nodes.append({"id": n.get("id"), "name": n.get("name"),
                          "state": _P.node_status(n), "pct": pct,
                          "depends_on": n.get("depends_on", [])})
            lines.append(f"- {n.get('name')} ({nodes[-1]['state']}, {pct}%)")
    # 下一步：locked 但前置已满足
    node_map = {n["id"]: n for n in nodes}
    ready = [n["name"] for n in nodes if n["state"] == "locked"
             and all(node_map.get(d, {}).get("state") in ("done", "learning")
                     for d in n["depends_on"] if d in node_map)]
    if ready:
        lines.append(f"可推进的下一步：{', '.join(ready[:5])}")
    return _ok("\n".join(lines))


def _search_knowledge(args, ctx):
    if not ctx.retriever:
        return _ok("（知识库未就绪，请先构建索引）")
    hits = ctx.retriever.search(args.get("query", ""), top_k=args.get("top_k", 5),
                                graph=ctx.graph, resume=ctx.resume)
    if not hits:
        return _ok("未检索到相关内容。")
    return _ok("\n".join(f'{h["ref"]} {h.get("source","")}:{h.get("symbol") or h.get("text","")[:60]}'
                         for h in hits))


# ── 写操作（生成建议，不写盘）──
def _add_node(args, ctx):
    """生成结构化 node 建议,过 schema 校验(失败 slugify 补 id/重写),emit node_proposal。"""
    import ai
    cfg = ctx.cfg or {}
    desc = args.get("description", "")
    existing = [n.get("id") for n in (ctx.graph.get("nodes") or [])]
    node = ai._norm_node(ai.generate_node(cfg, desc, "", existing))
    # id 不规范(非小写 a-z0-9_ / 大写或其它字符,如 _norm_node 由 name 合成的 "LightGCN")→ slugify(name) 补规范 id
    if node.get("name") and node.get("id") != ai.slugify_id(str(node.get("id"))):
        node["id"] = ai.slugify_id(str(node["name"]))
    ok, errs = ai.validate_node(node)
    if not ok:
        # 修补:缺 id 且有 name → slugify
        if "缺少 id" in errs and node.get("name"):
            node["id"] = ai.slugify_id(str(node["name"]))
            ok, errs = ai.validate_node(node)
        # 仍不 ok → 重写一次
        if not ok:
            try:
                node2 = ai._norm_node(ai.generate_node(cfg, desc, "", existing))
                if ai.validate_node(node2)[0]:
                    node = node2
            except Exception:
                pass
    event = {"type": "node_proposal", "mode": "new_node", "node": node}
    if not ai.validate_node(node)[0]:
        event["incomplete"] = True
    text = f"已生成新节点《{node.get('name', desc)}》建议（含 {len(node.get('tasks', []))} 个任务），请在卡片上确认。"
    return _ok(text, [event])


def _add_tasks(args, ctx):
    """为指定 node 生成补充 tasks/verify,emit node_proposal(add_tasks 模式)。"""
    import ai
    cfg = ctx.cfg or {}
    nid = args.get("node_id", "")
    desc = args.get("description", "")
    node = ai._norm_node(ai.generate_node(cfg, desc, nid, []))
    tasks = node.get("tasks", [])
    event = {"type": "node_proposal", "mode": "add_tasks", "node_id": nid, "tasks": tasks}
    text = f"已为节点 {nid} 生成 {len(tasks)} 条补充任务,请在卡片上确认。"
    return _ok(text, [event])


def _toggle_task(args, ctx):
    # 直接执行：通过 ctx 上的回调写回（由 loop 注入）
    cb = getattr(ctx, "on_toggle", None)
    if cb:
        ok = cb(args.get("tree_id"), args.get("node_id"), args.get("task_id"), args.get("done"))
        return _ok("已更新。" if ok else "更新失败：未找到该任务。")
    return _ok("（当前上下文不支持直接勾选）")


_REGISTRY = {
    "get_progress": _get_progress,
    "get_node": _get_node,
    "get_next": _get_next,
    "get_direction": _get_direction,
    "search_knowledge": _search_knowledge,
    "add_node": _add_node,
    "add_tasks": _add_tasks,
    "toggle_task": _toggle_task,
}
