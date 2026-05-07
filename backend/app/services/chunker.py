from typing import Any, Dict, List, Tuple

import tiktoken


DEFAULT_TARGET_TOKENS = 512
DEFAULT_OVERLAP_TOKENS = 64
ENCODER_NAME = "cl100k_base"
SEPARATORS = ["\n\n", "\n", ". ", "? ", "! ", "; ", " "]

_encoder = None


def get_encoder():
    global _encoder
    if _encoder is None:
        _encoder = tiktoken.get_encoding(ENCODER_NAME)
    return _encoder


def count_tokens(text: str) -> int:
    return len(get_encoder().encode(text))


def split_to_atoms(text: str, max_tokens: int, base_offset: int = 0) -> List[Tuple[str, int]]:
    if count_tokens(text) <= max_tokens:
        return [(text, base_offset)]

    for separator in SEPARATORS:
        if separator not in text:
            continue
        parts = text.split(separator)
        atoms: List[Tuple[str, int]] = []
        cursor = 0
        for index, part in enumerate(parts):
            is_last = index == len(parts) - 1
            piece = part + ("" if is_last else separator)
            if not piece:
                continue
            piece_offset = base_offset + cursor
            if count_tokens(piece) <= max_tokens:
                atoms.append((piece, piece_offset))
            else:
                atoms.extend(split_to_atoms(piece, max_tokens, piece_offset))
            cursor += len(piece)
        return atoms

    encoder = get_encoder()
    tokens = encoder.encode(text)
    out: List[Tuple[str, int]] = []
    char_pos = 0
    for start in range(0, len(tokens), max_tokens):
        slice_text = encoder.decode(tokens[start:start + max_tokens])
        out.append((slice_text, base_offset + char_pos))
        char_pos += len(slice_text)
    return out


def merge_atoms_into_chunks(
    atoms: List[Tuple[str, int]],
    target_tokens: int,
    overlap_tokens: int,
) -> List[Tuple[str, int, int]]:
    chunks: List[Tuple[str, int, int]] = []
    current_atoms: List[Tuple[str, int]] = []
    current_tokens = 0

    def emit_current():
        if not current_atoms:
            return
        chunk_text = "".join(text for text, _ in current_atoms)
        chunk_start = current_atoms[0][1]
        last_text, last_offset = current_atoms[-1]
        chunk_end = last_offset + len(last_text)
        chunks.append((chunk_text, chunk_start, chunk_end))

    for atom_text, atom_offset in atoms:
        atom_tokens = count_tokens(atom_text)

        if current_tokens + atom_tokens > target_tokens and current_atoms:
            emit_current()

            overlap_atoms: List[Tuple[str, int]] = []
            overlap_count = 0
            for prev_atom in reversed(current_atoms):
                prev_tokens = count_tokens(prev_atom[0])
                if overlap_atoms and overlap_count + prev_tokens > overlap_tokens:
                    break
                overlap_atoms.insert(0, prev_atom)
                overlap_count += prev_tokens
                if overlap_count >= overlap_tokens:
                    break

            current_atoms = list(overlap_atoms)
            current_tokens = overlap_count

        current_atoms.append((atom_text, atom_offset))
        current_tokens += atom_tokens

    emit_current()
    return chunks


def chunk_extraction(
    extraction: Dict[str, Any],
    doc_id: str,
    source_filename: str,
    target_tokens: int = DEFAULT_TARGET_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []
    chunk_index = 0

    pages = extraction.get("pages") or []
    if not pages and extraction.get("full_text"):
        pages = [{"page_number": 1, "text": extraction["full_text"]}]

    for page in pages:
        page_text = page.get("text") or ""
        if not page_text.strip():
            continue
        page_number = page.get("page_number", 1)

        atoms = split_to_atoms(page_text, target_tokens)
        page_chunks = merge_atoms_into_chunks(atoms, target_tokens, overlap_tokens)

        for chunk_text, char_start, char_end in page_chunks:
            chunks.append(
                {
                    "chunk_id": f"{doc_id}:p{page_number}:c{chunk_index}",
                    "doc_id": doc_id,
                    "text": chunk_text,
                    "token_count": count_tokens(chunk_text),
                    "page_number": page_number,
                    "chunk_index": chunk_index,
                    "char_start": char_start,
                    "char_end": char_end,
                    "source_filename": source_filename,
                }
            )
            chunk_index += 1

    return chunks


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    from app.services.pdf_extractor import extract_pdf_text

    target = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(__file__).resolve().parent.parent.parent.parent / "assets" / "testocr" / "3.pdf"
    )
    extraction = extract_pdf_text(target)
    chunks = chunk_extraction(extraction, doc_id="test-doc", source_filename=target.name)

    print(f"Total chunks: {len(chunks)}")
    for chunk in chunks:
        print(f"  [{chunk['chunk_id']}] page {chunk['page_number']}, tokens {chunk['token_count']}, chars {chunk['char_start']}-{chunk['char_end']}")
        print(f"    preview: {chunk['text'][:120]!r}")
