"""Zep Cloud memory: thread history + fact context for personalization."""

from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv
from zep_cloud.client import Zep
from zep_cloud.types import Message

load_dotenv()

ZEP_API_KEY = os.getenv("ZEP_API") or os.getenv("ZEP_API_KEY")


class ZepMemory:
    def __init__(self, api_key: Optional[str] = None):
        key = api_key or ZEP_API_KEY
        if not key:
            raise ValueError("Thiếu ZEP_API hoặc ZEP_API_KEY trong .env")
        self._client = Zep(api_key=key)

    @property
    def client(self) -> Zep:
        return self._client

    def ensure_user(
        self,
        user_id: str,
        *,
        first_name: str = "SinhVien",
        ma_sv: str | None = None,
    ) -> None:
        """user_id = maSV của sinh viên đang đăng nhập."""
        try:
            self._client.user.get(user_id=user_id)
        except Exception:
            self._client.user.add(
                user_id=user_id,
                first_name=first_name,
                email=f"{(ma_sv or user_id)}@sis.haui.edu.vn",
            )

    def ensure_thread(self, thread_id: str, user_id: str) -> None:
        try:
            self._client.thread.get(thread_id=thread_id)
        except Exception:
            self._client.thread.create(thread_id=thread_id, user_id=user_id)

    def get_context(self, thread_id: str, *, last_n: int = 10) -> str:
        try:
            memory_result = self._client.memory.get(
                session_id=thread_id,
                last_n=last_n,
                min_rating=0.7,
            )
            if memory_result.context:
                return memory_result.context.strip()
        except Exception:
            pass
        return ""

    def get_hybrid_context(self, user_id: str, thread_id: str, query: str) -> str:
        base = self.get_context(thread_id)
        if base:
            return base
        try:
            search_results = self._client.graph.search(
                user_id=user_id,
                query=query,
                scope="edges",
                limit=5,
            )
            facts = []
            for result in search_results or []:
                if hasattr(result, "data") and hasattr(result.data, "fact"):
                    facts.append(result.data.fact)
            return "\n".join(facts)
        except Exception:
            return ""

    def add_exchange(self, thread_id: str, user_text: str, assistant_text: str) -> None:
        messages = [
            Message(role="user", content=user_text),
            Message(role="assistant", content=assistant_text),
        ]
        self._client.thread.add_messages(thread_id=thread_id, messages=messages)

    def get_recent_messages(self, thread_id: str, limit: int = 6) -> list[dict[str, str]]:
        try:
            thread = self._client.thread.get(thread_id=thread_id)
            out: list[dict[str, str]] = []
            for msg in (thread.messages or [])[-limit:]:
                if msg.role in ("user", "assistant") and msg.content:
                    out.append({"role": msg.role, "content": msg.content})
            return out
        except Exception:
            return []


def ensure_zep_session(
    zep: ZepMemory,
    user_id: str,
    thread_id: str,
    *,
    ho_ten: str | None = None,
) -> None:
    zep.ensure_user(user_id, first_name=ho_ten or "SinhVien", ma_sv=user_id)
    zep.ensure_thread(thread_id, user_id)
