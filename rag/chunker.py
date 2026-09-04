def chunk_documents(extracted_items, chunk_size=800, chunk_overlap=100):
    """
    Takes the list of dicts returned by any extract_text_from_* function
    and splits long text into smaller overlapping chunks.

    extracted_items: list of dicts, each with at least 'text' and 'source'
    chunk_size: max characters per chunk
    chunk_overlap: characters shared between consecutive chunks (keeps context across a split)
    """
    chunks = []

    for item in extracted_items:
        text = item["text"]
        source = item["source"]
        location = {k: v for k, v in item.items() if k not in ("text", "source")}

        if len(text) <= chunk_size:
            chunks.append({"text": text, "source": source, **location})
            continue

        start = 0
        while start < len(text):
            end = start + chunk_size
            piece = text[start:end].strip()
            if piece:
                chunks.append({"text": piece, "source": source, **location})
            start += chunk_size - chunk_overlap

    return chunks