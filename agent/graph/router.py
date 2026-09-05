"""
router.py — Deterministic Request Router for Member 2 Agent Workflow
"""


def route_request_intent(user_request: str) -> str:
    """Deterministically routes user_request into one of: 'general', 'pid', 'knowledge', 'document', or 'unknown'."""
    text = user_request.lower().strip()

    if not text:
        return "unknown"

    # Greetings & conversational openers explicitly map to general
    greetings = [
        "hello",
        "hi",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
        "how are you",
        "greetings",
        "howdy",
        "hi there",
        "hello there",
    ]
    if any(text == g or text.startswith(g + " ") for g in greetings):
        return "general"

    # Specific routes prioritized first
    pid_keywords = [
        "p&id",
        "pid",
        "drawing",
        "piping diagram",
        "process diagram",
        "schematic",
        "valve position",
        "piping & instrumentation",
    ]
    if any(kw in text for kw in pid_keywords):
        return "pid"

    knowledge_keywords = [
        "api ",
        "api-",
        "iso ",
        "iso-",
        "standard",
        "specification",
        "regulation",
        "according to",
        "code requirement",
    ]
    if any(kw in text for kw in knowledge_keywords):
        return "knowledge"

    document_keywords = [
        "report",
        "excel",
        "spreadsheet",
        "pdf",
        "docx",
        "doc",
        "doc's",
        "document",
        "word",
        "export",
        "generate report",
        "create document",
    ]
    if any(kw in text for kw in document_keywords):
        return "document"

    # General conversational and question patterns
    general_keywords = [
        "what",
        "explain",
        "how",
        "why",
        "describe",
        "purpose",
        "define",
        "tell me",
        "can you",
        "could you",
        "summarize",
    ]
    if any(kw in text for kw in general_keywords):
        return "general"

    # Fallback to general if multi-word query or single word with 3+ alphabetic chars
    words = text.split()
    if len(words) >= 2 or (len(words) == 1 and len(words[0]) >= 3 and words[0].isalpha()):
        return "general"

    return "unknown"
