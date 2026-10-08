import re
from pathlib import Path

import yaml

from config import settings
from domain import Document

# Optional YAML front matter block at the very start of a document:
# ---\nkey: value\n...\n---\n  (US4/T029 — metadata for generic filters)
_FRONT_MATTER_RE = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*\n", re.DOTALL)


def split_front_matter(content: str) -> tuple[dict, str]:
    """Split optional YAML front matter into (metadata, content).

    Content without a front matter block is returned unchanged with an
    empty metadata dict. Invalid YAML front matter fails loudly — never
    silently dropped (Principle VII).
    """
    match = _FRONT_MATTER_RE.match(content)
    if not match:
        return {}, content
    data = yaml.safe_load(match.group(1))
    if data is None:
        data = {}
    if not isinstance(data, dict):
        msg = f"front matter must be a YAML mapping, got {type(data).__name__}"
        raise ValueError(msg)
    return dict(data), content[match.end() :]


def discover_documents(document_dir: str | None = None) -> list[Document]:
    """Discover .md files under DOCUMENT_DIR, assign document_id, preserve
    document_name and source, return Document objects.

    YAML front matter (if present) is parsed into Document.metadata and
    stripped from the content.

    Clear error if directory missing or no files (exit 1 path).
    """
    dir_path = Path(document_dir or settings.document_dir)

    if not dir_path.exists():
        msg = f"Document directory not found: {dir_path}"
        raise FileNotFoundError(msg)

    if not dir_path.is_dir():
        msg = f"Document path is not a directory: {dir_path}"
        raise NotADirectoryError(msg)

    md_files = sorted(dir_path.glob("*.md"))

    if not md_files:
        msg = f"No Markdown files found in {dir_path}"
        raise FileNotFoundError(msg)

    documents: list[Document] = []
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            metadata, body = split_front_matter(content)
            # Generate a stable document_id from the filename
            document_id = re.sub(r"\.md$", "", md_file.name)
            document_name = md_file.name
            source = str(md_file)

            doc = Document(
                document_id=document_id,
                document_name=document_name,
                source=source,
                content=body,
                metadata=metadata,
            )
            documents.append(doc)
        except Exception as e:
            msg = f"Failed to load document {md_file}: {e}"
            raise RuntimeError(msg) from e

    return documents
