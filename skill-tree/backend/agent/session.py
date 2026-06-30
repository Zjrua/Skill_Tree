"""agent/session.py — 单用户会话内存管理（多轮历史 + 图谱快照 + TTL）。"""
from __future__ import annotations
import time
from dataclasses import dataclass, field


@dataclass
class Session:
    uid: str
    messages: list[dict] = field(default_factory=list)
    graph_snapshot: dict | None = None
    last_active: float = field(default_factory=time.time)


class SessionStore:
    def __init__(self, ttl: int = 1800):
        self.ttl = ttl
        self._sessions: dict[str, Session] = {}

    def get_or_create(self, uid: str) -> Session:
        now = time.time()
        s = self._sessions.get(uid)
        if s is not None and (now - s.last_active) <= self.ttl:
            s.last_active = now
            return s
        # 过期或不存在 → 新建
        s = Session(uid=uid)
        self._sessions[uid] = s
        return s

    def clear(self, uid: str) -> None:
        self._sessions.pop(uid, None)
