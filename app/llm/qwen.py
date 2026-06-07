from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.config import get_settings


class QwenClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class RerankResult:
    index: int
    relevance_score: float


def chat_completion(messages: list[dict[str, str]], temperature: float = 1) -> str:
    model = _init_qwen_chat_model(temperature=temperature)
    try:
        response = model.invoke(_to_langchain_messages(messages))
    except Exception as exc:
        raise QwenClientError(f"Qwen API request failed: {exc}") from exc

    content = _content_to_text(response.content)
    if not isinstance(content, str) or not content.strip():
        raise QwenClientError("Qwen API returned empty message content.")
    return content.strip()


def chat_completion_stream(messages: list[dict[str, str]], temperature: float = 1) -> Iterator[str]:
    model = _init_qwen_chat_model(temperature=temperature)
    has_content = False
    try:
        for chunk in model.stream(_to_langchain_messages(messages)):
            content = _content_to_text(getattr(chunk, "content", ""))
            if content:
                has_content = True
                yield content
    except Exception as exc:
        raise QwenClientError(f"Qwen API streaming request failed: {exc}") from exc

    if not has_content:
        raise QwenClientError("Qwen API returned empty streaming content.")


def _init_qwen_chat_model(temperature: float):
    settings = get_settings()
    api_key = settings.dashscope_api_key
    if not api_key:
        raise QwenClientError("QWEN_API_KEY or DASHSCOPE_API_KEY is not configured.")

    return init_chat_model(
        settings.qwen_model,
        model_provider="openai",
        base_url=str(settings.qwen_base_url),
        api_key=api_key,
        temperature=temperature,
    )


def _content_to_text(content: object) -> str:
    if isinstance(content, list):
        return "".join(
            str(part.get("text", ""))
            if isinstance(part, dict)
            else str(part)
            for part in content
        )
    if isinstance(content, str):
        return content
    return str(content) if content is not None else ""


def _to_langchain_messages(messages: list[dict[str, str]]) -> list[SystemMessage | HumanMessage | AIMessage]:
    converted: list[SystemMessage | HumanMessage | AIMessage] = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        if role == "system":
            converted.append(SystemMessage(content=content))
        elif role == "assistant":
            converted.append(AIMessage(content=content))
        else:
            converted.append(HumanMessage(content=content))
    return converted


def rerank_documents(query: str, documents: list[str], top_n: int = 5) -> list[RerankResult]:
    settings = get_settings()
    api_key = settings.dashscope_api_key
    if not api_key:
        raise QwenClientError("QWEN_API_KEY or DASHSCOPE_API_KEY is not configured.")
    if not documents:
        return []

    base_url = str(settings.qwen_rerank_base_url).rstrip("/")
    request = Request(
        f"{base_url}/reranks",
        data=json.dumps(
            {
                "model": settings.qwen_rerank_model,
                "query": query,
                "documents": documents,
                "top_n": min(max(top_n, 1), len(documents)),
                "return_documents": False,
                "instruct": "Given an enterprise knowledge-base query, retrieve relevant passages that answer the query.",
            },
            ensure_ascii=False,
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise QwenClientError(f"Qwen rerank API returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise QwenClientError(f"Qwen rerank API request failed: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise QwenClientError("Qwen rerank API returned invalid JSON.") from exc

    results = payload.get("results")
    if not isinstance(results, list):
        raise QwenClientError("Qwen rerank API response missing results.")

    reranked: list[RerankResult] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        index = item.get("index")
        score = item.get("relevance_score")
        if isinstance(index, int) and isinstance(score, int | float):
            reranked.append(RerankResult(index=index, relevance_score=float(score)))

    reranked.sort(key=lambda item: item.relevance_score, reverse=True)
    return reranked
