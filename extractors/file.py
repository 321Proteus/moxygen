from .common import base_info, load_compounddef, members, prune, refs


def extract_file(ref: str) -> dict:
    """Extract a Doxygen file (by refid or file name). Source listing is omitted."""
    cd = load_compounddef(ref, "file")
    
    return prune({
        **base_info(cd),
        "includes": refs(cd, "includes"),
        "included_by": refs(cd, "includedby"),
        "inner_namespaces": refs(cd, "innernamespace"),
        "inner_classes": refs(cd, "innerclass"),
        "members": members(cd),
    })
