from dataclasses import dataclass
from pathlib import Path

import fitz # PyMuPDF 库，Python 处理 PDF 的王牌库，专门读写、解析 PDF 文件。


@dataclass(frozen=True)
class ParsedPage:
    page_number: int
    content: str


@dataclass(frozen=True)
class ParsedPdf:
    page_count: int
    pages: list[ParsedPage]


def parse_pdf(file_path: Path) -> ParsedPdf:
    """
    解析 PDF 文件，提取每一页的文本内容。
    参数:
        file_path: PDF 文件的路径
    返回:
        ParsedPdf 对象，包含总页数和每页的解析结果
    """
    pages: list[ParsedPage] = []

    # 使用 PyMuPDF 打开 PDF 文件
    with fitz.open(file_path) as document:
        # 遍历 PDF 的每一页，页码从 1 开始
        for page_index, page in enumerate(document, start=1):
            # 提取当前页的纯文本内容并去除首尾空白
            text = page.get_text("text").strip()
            # 如果页面有文本内容，则创建 ParsedPage 对象
            if text:
                pages.append(ParsedPage(page_number=page_index, content=text))
        # 返回包含页数和所有页面内容的 ParsedPdf 对象
        return ParsedPdf(page_count=document.page_count, pages=pages)
