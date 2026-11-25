from .common import base_info, load_compounddef, members, prune, refs, template_params


def extract_class_like(ref: str, kind: str) -> dict:
    
    cd = load_compounddef(ref, kind)

    return prune({
        **base_info(cd),
        "prot": cd.get("prot"),
        "template_params": template_params(cd),
        "bases": refs(cd, "basecompoundref"),
        "derived": refs(cd, "derivedcompoundref"),
        "inner_classes": refs(cd, "innerclass"),
        "members": members(cd),
    })


def extract_class(ref: str) -> dict:
    """Extract a Doxygen class (by refid or qualified name)."""
    return extract_class_like(ref, "class")
