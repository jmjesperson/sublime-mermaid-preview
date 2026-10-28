"""Choose which text to render: the selection if there is one, otherwise the whole document."""

NOTHING_TO_RENDER = "nothing to render (the text is empty)"
FIRST_SELECTION_ONLY = "rendered the first selection only"


def pick_source(selected_texts: list[str], whole_text: str) -> tuple[str | None, str | None]:
    """Return (text_to_render, status_note). The text is None when there is nothing to render."""
    selected = [text for text in selected_texts if text]
    text = selected[0] if selected else whole_text
    if not text.strip():
        return None, NOTHING_TO_RENDER
    note = FIRST_SELECTION_ONLY if len(selected) > 1 else None
    return text, note
