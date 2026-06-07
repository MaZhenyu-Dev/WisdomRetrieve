from __future__ import annotations

import re
from typing import Protocol

from app.llm.qwen import QwenClientError, chat_completion


class HistoryMessage(Protocol):
    role: str
    content: str


def rewrite_query(question: str, history: list[HistoryMessage], max_history: int = 6) -> str:
    question = question.strip()
    if not question or not history:
        return question

    history_text = "\n".join(
        f"{'用户' if row.role == 'user' else '助手'}: {row.content}"
        for row in history[-max_history:]
    )
    messages = [
        {
            "role": "system",
            "content": (
                "你是企业知识库问答系统的检索查询改写器。"
                "根据最近对话，把用户当前问题改写成完整、独立、适合检索的中文问题。"
                "如果当前问题已经完整，保持原意即可。"
                "只输出改写后的问题，不要解释。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"最近对话:\n{history_text}\n\n"
                f"当前问题: {question}\n\n"
                "改写后的检索问题:"
            ),
        },
    ]

    try:
        rewritten = chat_completion(messages, temperature=0.0)
    except QwenClientError:
        return _heuristic_rewrite(question, history)

    rewritten = _clean_rewritten_query(rewritten)
    if not rewritten:
        return _heuristic_rewrite(question, history)
    return rewritten[:500]


def _heuristic_rewrite(question: str, history: list[HistoryMessage]) -> str:
    if not _looks_elliptical(question):
        return question

    previous_user_question = _last_user_question(history)
    if not previous_user_question:
        return question
    return f"关于“{previous_user_question}”，{question}"


def _looks_elliptical(question: str) -> bool:
    stripped = question.strip()
    if len(stripped) <= 12:
        return True
    return bool(re.search(r"(呢|这个|那个|它|上述|前面|报销呢|标准呢)[？?]?$", stripped))


def _last_user_question(history: list[HistoryMessage]) -> str | None:
    for row in reversed(history):
        if row.role == "user" and row.content.strip():
            return row.content.strip()
    return None


def _clean_rewritten_query(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^改写后的检索问题[:：]\s*", "", cleaned)
    cleaned = cleaned.strip("\"'“”` \n")
    return cleaned
