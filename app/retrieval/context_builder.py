from __future__ import annotations

import re

from app.retrieval.chroma_store import RetrievedChunk


def build_context(chunks: list[RetrievedChunk], max_chars: int = 6000) -> str:
    if not chunks:
        return ""

    blocks: list[str] = []
    remaining = max(max_chars, 1000)
    previous_normalized = ""

    for index, chunk in enumerate(chunks, start=1):
        content = _dedupe_adjacent_repeats(chunk.content)
        normalized = _normalize(content)
        if normalized and normalized == previous_normalized:
            continue
        previous_normalized = normalized

        metadata = chunk.metadata
        score_text = _format_scores(chunk)
        block = (
            f"[来源{index}]\n"
            f"文件: {metadata.get('file_name', '')}\n"
            f"页码: {metadata.get('page_number', '')}\n"
            f"标题: {metadata.get('title', '')}\n"
            f"Chunk: {metadata.get('chunk_index', '')}\n"
            f"召回: {','.join(chunk.retrieval_sources) or 'unknown'}{score_text}\n"
            f"内容: {content}"
        )

        if len(block) > remaining:
            if remaining < 300:
                break
            block = block[: remaining - 3].rstrip() + "..."
        blocks.append(block)
        remaining -= len(block) + 2
        if remaining <= 0:
            break

    return "\n\n".join(blocks)


def _dedupe_adjacent_repeats(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    deduped_lines: list[str] = []
    previous = ""
    for line in lines:
        normalized = _normalize(line)
        if normalized and normalized == previous:
            continue
        deduped_lines.append(line)
        previous = normalized

    paragraphs = re.split(r"\n\s*\n", "\n".join(deduped_lines))
    deduped_paragraphs: list[str] = []
    previous = ""
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        normalized = _normalize(paragraph)
        if normalized and normalized == previous:
            continue
        if paragraph:
            deduped_paragraphs.append(paragraph)
        previous = normalized
    return "\n\n".join(deduped_paragraphs)


def _format_scores(chunk: RetrievedChunk) -> str:
    score_parts = []
    for name in ("vector", "bm25", "hybrid", "rerank"):
        score = chunk.scores.get(name)
        if score is not None:
            score_parts.append(f"{name}={score:.4f}")
    return f" ({'; '.join(score_parts)})" if score_parts else ""


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()
