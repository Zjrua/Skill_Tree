# tests/test_session.py
from __future__ import annotations
import time

from agent.session import SessionStore, Session


def test_get_or_create_returns_same_session():
    store = SessionStore(ttl=60)
    s1 = store.get_or_create("user-a")
    s2 = store.get_or_create("user-a")
    assert s1 is s2
    assert s1.uid == "user-a"
    assert s1.messages == []


def test_append_message_and_snapshot():
    store = SessionStore(ttl=60)
    s = store.get_or_create("user-a")
    s.messages.append({"role": "user", "content": "hi"})
    s2 = store.get_or_create("user-a")
    assert s2.messages == [{"role": "user", "content": "hi"}]


def test_expired_session_is_cleared():
    store = SessionStore(ttl=0)  # 立即过期
    s = store.get_or_create("user-a")
    s.messages.append({"role": "user", "content": "old"})
    time.sleep(0.01)
    s2 = store.get_or_create("user-a")
    assert s2.messages == []  # 过期后是全新 session
    assert s2 is not s


def test_clear():
    store = SessionStore(ttl=60)
    store.get_or_create("user-a")
    store.clear("user-a")
    assert "user-a" not in store._sessions
