from .common import base_info, load_compounddef, prune, refs


def extract_dir(ref: str) -> dict:
    """Extract a Doxygen directory (by refid or path such as 'src/db/til')."""

    cd = load_compounddef(ref, "dir")
    
    return prune({
        **base_info(cd),
        "subdirs": refs(cd, "innerdir"),
        "files": refs(cd, "innerfile"),
    })
