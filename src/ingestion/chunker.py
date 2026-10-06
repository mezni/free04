
from domain import Chunk, Document


def chunk_document(
    document: Document,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[Chunk]:
    """Fixed-size character chunking with CHUNK_SIZE/CHUNK_OVERLAP, produce
    Chunk objects carrying chunk_id, content, and inherited metadata
    (document_id, document_name, source).

    A document smaller than one chunk produces exactly one chunk (edge case).
    """
    cs = chunk_size if chunk_size is not None else 500
    co = chunk_overlap if chunk_overlap is not None else 50

    if cs <= 0:
        raise ValueError(f"chunk_size must be > 0, got {cs}")
    if co < 0:
        raise ValueError(f"chunk_overlap must be >= 0, got {co}")
    if co >= cs:
        raise ValueError(f"chunk_overlap must be < chunk_size ({cs}), got {co}")

    content = document.content
    doc_id = document.document_id
    doc_name = document.document_name
    source = document.source

    if not content.strip():
        # Edge case: empty document produces one empty chunk
        # But validation in Domain should catch this; return minimal chunk
        return [
            Chunk(
                chunk_id=f"{doc_id}#0000",
                content="",
                document_id=doc_id,
                document_name=doc_name,
                source=source,
                chunk_index=0,
            )
        ]

    chunks: list[Chunk] = []
    start = 0
    chunk_index = 0

    while start < len(content):
        end = start + cs
        chunk_content = content[start:end]

        chunk_index += 1
        chunk_id = f"{doc_id}#{chunk_index:04d}"

        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                content=chunk_content,
                document_id=doc_id,
                document_name=doc_name,
                source=source,
                chunk_index=chunk_index,
            )
        )

        if end >= len(content):
            break

        start = end - co  # move forward with overlap

    return chunks