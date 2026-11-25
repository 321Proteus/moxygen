from .common import base_info, load_compounddef, members, prune, refs


def extract_namespace(ref: str) -> dict:
    """Extract a Doxygen namespace (by refid or qualified name)."""
    cd = load_compounddef(ref, "namespace")
    
    return prune({
        **base_info(cd),
        "inner_namespaces": refs(cd, "innernamespace"),
        "inner_classes": refs(cd, "innerclass"),
        "members": members(cd),
    })
