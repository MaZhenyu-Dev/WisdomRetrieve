from dataclasses import dataclass

from langchain_core.documents import Document as LangChainDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.parser.pdf import ParsedPage


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    page_number: int
    content: str
    title: str | None = None


def split_pages(
    pages: list[ParsedPage],
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> list[TextChunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", "；", ";", ".", " ", ""],
        add_start_index=True,
    )

    documents: list[LangChainDocument] = []
    for page in pages:
        content = _normalize_text(page.content)
        if not content:
            continue

        documents.append(
            LangChainDocument(
                page_content=content,
                metadata={
                    "page_number": page.page_number,
                    "title": _guess_title(content),
                },
            )
        )

    split_documents = splitter.split_documents(documents)
    chunks: list[TextChunk] = []
    for chunk_index, document in enumerate(split_documents):
        content = document.page_content.strip()
        if not content:
            continue
        chunks.append(
            TextChunk(
                chunk_index=chunk_index,
                page_number=int(document.metadata["page_number"]),
                title=document.metadata.get("title"),
                content=content,
            )
        )
    return chunks


def _normalize_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _guess_title(text: str) -> str | None:
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line[:255]
    return None
