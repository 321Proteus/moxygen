from .class_ import extract_class_like


def extract_struct(ref: str) -> dict:
    """Extract a Doxygen struct (by refid or qualified name)."""
    return extract_class_like(ref, "struct")
