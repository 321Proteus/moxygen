from .common import base_info, load_compounddef, paragraphs, prune, refs, text


def _sections(el) -> list[dict]:
    out = []

    for s in el.iter():
        if s.tag in ("sect1", "sect2", "sect3", "sect4"):
            out.append({"level": int(s.tag[-1]), "id": s.get("id"), "title": text(s.find("title"))})
    
    return out


def extract_page(ref: str) -> dict:
    """Extract a Doxygen page (by refid or name, e.g. 'index', 'todo')."""

    cd = load_compounddef(ref, "page")

    detail = cd.find("detaileddescription")
    info = base_info(cd)
    info.pop("detailed")  # the same as "content"

    return prune({
        **info,
        "title": text(cd.find("title")),
        "sections": _sections(detail) if detail is not None else [],
        "inner_pages": refs(cd, "innerpage"),
        "content": paragraphs(detail),
    })
