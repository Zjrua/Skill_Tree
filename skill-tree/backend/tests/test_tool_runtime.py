# tests/test_tool_runtime.py
from __future__ import annotations

from agent.tool_runtime import Context, execute_tool, ToolError, ToolResult


def _ctx(graph=None, resume=None, retriever=None, trees=None):
    return Context(uid="u", graph=graph or {}, resume=resume,
                   retriever=retriever, rag_index_dir=None, trees=trees)


def test_get_progress_from_graph():
    graph = {"nodes": [{"id": "deepfm", "name": "DeepFM", "state": "learning", "pct": 50,
                        "mastered": 2, "total_points": 4}],
             "overview": {"overall_pct": 45}}
    out = execute_tool("get_progress", {}, _ctx(graph=graph))
    assert "45" in out["text"]
    assert "deepfm" in out["text"] or "DeepFM" in out["text"]


def test_get_node_missing_returns_hint():
    out = execute_tool("get_node", {"node_id": "nope"}, _ctx(graph={"nodes": []}))
    assert "nope" in out["text"]


def test_unknown_tool_raises():
    try:
        execute_tool("bogus", {}, _ctx())
        assert False, "应抛 ToolError"
    except ToolError:
        pass


def test_add_node_returns_proposal_not_written():
    """add_node 返回 ToolResult,text 含'确认/建议'标记,不写盘。"""
    import ai
    orig = ai.generate_node
    ai.generate_node = lambda cfg, d, nid, e: {"id": "x", "name": "X", "tasks": []}
    try:
        out = execute_tool("add_node", {"description": "LightGCN"}, _ctx())
    finally:
        ai.generate_node = orig
    assert "确认" in out["text"] or "建议" in out["text"]


def test_get_direction_returns_nodes_and_next():
    """get_direction 返回方向所有节点 + 进度 + 可推进的下一步。"""
    trees = [{"tree_id": "agent", "title": "AI Agent", "icon": "🤖",
              "branches": [{"id": "b", "name": "Agent", "nodes": [
                  {"id": "transformer", "name": "Transformer", "category": "x",
                   "depends_on": [], "tasks": [{"id": "t", "title": "读论文", "done": True}]},
                  {"id": "react", "name": "ReAct", "category": "x",
                   "depends_on": ["transformer"], "tasks": [{"id": "t", "title": "x", "done": False}]},
              ]}]}]
    out = execute_tool("get_direction", {"dir_id": "agent"}, _ctx(trees=trees))
    assert "AI Agent" in out["text"]
    assert "Transformer" in out["text"]
    assert "ReAct" in out["text"]
    assert "可推进的下一步" in out["text"]   # react 前置 transformer 已 done


def test_get_direction_unknown_returns_hint():
    out = execute_tool("get_direction", {"dir_id": "不存在"}, _ctx(trees=[]))
    assert "未找到" in out["text"]


def test_execute_tool_returns_tool_result_dict():
    """execute_tool 返回 {text, events},events 默认空 list。"""
    graph = {"nodes": [{"id": "deepfm", "name": "DeepFM", "state": "learning", "pct": 50,
                        "mastered": 2, "total_points": 4}],
             "overview": {"overall_pct": 45}}
    out = execute_tool("get_progress", {}, _ctx(graph=graph))
    assert isinstance(out, dict)
    assert "text" in out and "45" in out["text"]
    assert out.get("events") == []


def test_add_node_emits_proposal_event():
    """add_node 返回 ToolResult,events 含 node_proposal,node 通过校验。"""
    import ai
    orig = ai.generate_node
    ai.generate_node = lambda cfg, description, node_id, existing_ids: {
        "id": "lightgcn", "name": "LightGCN", "category": "推荐",
        "status": "locked", "depends_on": [], "tasks": [{"id": "t1", "title": "读论文", "done": False}]}
    try:
        ctx = _ctx()
        ctx.cfg = {"base_url": "x", "api_key": "y"}
        out = execute_tool("add_node", {"description": "LightGCN"}, ctx)
    finally:
        ai.generate_node = orig
    assert out["text"]
    assert any(e.get("type") == "node_proposal" for e in out["events"])
    prop = [e for e in out["events"] if e.get("type") == "node_proposal"][0]
    assert prop["mode"] == "new_node"
    assert prop["node"]["id"] == "lightgcn"
    assert prop["node"]["name"] == "LightGCN"


def test_add_node_invalid_then_autofixed_by_slugify():
    """第一次生成的 node 缺 id(校验失败),用 slugify(name) 补 id。"""
    import ai
    orig = ai.generate_node
    ai.generate_node = lambda cfg, d, nid, e: {"name": "LightGCN", "tasks": []}  # 缺 id
    try:
        ctx = _ctx()
        ctx.cfg = {"base_url": "x", "api_key": "y"}
        out = execute_tool("add_node", {"description": "LightGCN"}, ctx)
    finally:
        ai.generate_node = orig
    prop = [e for e in out["events"] if e.get("type") == "node_proposal"][0]
    assert prop["node"]["id"] == "lightgcn"   # slugified from name


def test_add_tasks_emits_proposal_event():
    """add_tasks 产 add_tasks 模式的 node_proposal。"""
    import ai
    orig = ai.generate_node
    ai.generate_node = lambda cfg, d, nid, e: {"id": nid or "n", "name": "N",
                                               "tasks": [{"id": "t2", "title": "新任务", "done": False}]}
    try:
        ctx = _ctx()
        ctx.cfg = {"base_url": "x", "api_key": "y"}
        out = execute_tool("add_tasks", {"node_id": "n1", "description": "补手算验收"}, ctx)
    finally:
        ai.generate_node = orig
    assert any(e.get("type") == "node_proposal" for e in out["events"])
    prop = [e for e in out["events"] if e.get("type") == "node_proposal"][0]
    assert prop["mode"] == "add_tasks"
    assert prop["node_id"] == "n1"
