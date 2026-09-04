# Keys that represent a *position within* a document, not a distinct group.
# Chunks can merge across different values of these keys, tracked as a from/to range.
POSITION_KEYS = {"page", "section", "row"}


def _locations_compatible(a, b):
    """
    Two location dicts can be merged if every non-position key matches
    (e.g. same 'sheet' for Excel). Position keys like page/section/row
    are allowed to differ — that's exactly what we're merging across.
    """
    for key in set(a) | set(b):
        if key in POSITION_KEYS:
            continue
        if a.get(key) != b.get(key):
            return False
    return True


def chunk_documents(extracted_items, chunk_size=800, chunk_overlap=100):
    """
    Takes the list of dicts returned by any extract_text_from_* function.
    - Merges consecutive small pieces from the same source (and same group,
      e.g. same Excel sheet) into fuller chunks, up to chunk_size.
    - Splits any single piece longer than chunk_size into overlapping chunks.
    """
    chunks = []
    buffer_text = ""
    buffer_source = None
    buffer_start_loc = None
    buffer_end_loc = None

    def flush():
        nonlocal buffer_text, buffer_source, buffer_start_loc, buffer_end_loc
        if buffer_text.strip():
            meta = {}
            for key in buffer_start_loc:
                start_val = buffer_start_loc[key]
                end_val = buffer_end_loc.get(key, start_val)
                if start_val == end_val:
                    meta[key] = start_val
                else:
                    meta[f"{key}_from"] = start_val
                    meta[f"{key}_to"] = end_val
            chunks.append({"text": buffer_text.strip(), "source": buffer_source, **meta})
        buffer_text = ""
        buffer_source = None
        buffer_start_loc = None
        buffer_end_loc = None

    for item in extracted_items:
        text = item["text"].strip()
        if not text:
            continue

        source = item["source"]
        location = {k: v for k, v in item.items() if k not in ("text", "source")}

        # Oversized single item: flush whatever's buffered, then split this one alone
        if len(text) > chunk_size:
            flush()
            start = 0
            while start < len(text):
                end = start + chunk_size
                piece = text[start:end].strip()
                if piece:
                    chunks.append({"text": piece, "source": source, **location})
                start += chunk_size - chunk_overlap
            continue

        can_merge = (
            buffer_source == source
            and buffer_end_loc is not None
            and _locations_compatible(buffer_end_loc, location)
            and len(buffer_text) + len(text) + 1 <= chunk_size
        )

        if can_merge:
            buffer_text += "\n" + text
            buffer_end_loc = location
        else:
            flush()
            buffer_text = text
            buffer_source = source
            buffer_start_loc = location
            buffer_end_loc = location

    flush()
    return chunks