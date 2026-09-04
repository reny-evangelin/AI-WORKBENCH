def create_metadata(source, page=None, section=None, sheet=None, row=None):
    metadata = {
        "source": source
    }

    if page is not None:
        metadata["page"] = page

    if section is not None:
        metadata["section"] = section

    if sheet is not None:
        metadata["sheet"] = sheet

    if row is not None:
        metadata["row"] = row

    return metadata