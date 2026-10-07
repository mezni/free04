import re
from pathlib import Path

from config import settings
from domain import Document


def discover_documents(document_dir: str | None = None) -> list[Document]:
    """Discover .md files under DOCUMENT_DIR, assign document_id, preserve
    document_name and source, return Document objects.

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
            # Generate a stable document_id from the filename
            document_id = re.sub(r"\.md$", "", md_file.name)
            document_name = md_file.name
            source = str(md_file)

            doc = Document(
                document_id=document_id,
                document_name=document_name,
                source=source,
                content=content,
            )
            documents.append(doc)
        except Exception as e:
            msg = f"Failed to load document {md_file}: {e}"
            raise RuntimeError(msg) from e

    return documents
