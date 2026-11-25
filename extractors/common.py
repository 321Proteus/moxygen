"""Shared helpers for reading Doxygen XML."""
import os
import xml.etree.ElementTree as etree
from functools import lru_cache
from pathlib import Path

ENV_VAR = "MOXYGEN_XML_DIR"
DEFAULT_REL = Path("docs") / "xml"

_explicit: Path | None = None  # set from --xml-dir


def set_xml_dir(path: str | os.PathLike | None) -> None:
    """Pin the XML directory (e.g. from a CLI argument); None restores auto-detection."""
    global _explicit
    _explicit = Path(path).expanduser() if path else None


def get_xml_dir() -> Path:
    """Resolve the Doxygen XML directory: --xml-dir, then $MOXYGEN_XML_DIR, then ./docs/xml.

    Resolved on every call so the server notices a directory that appears later,
    and relative paths follow the project the server was launched in.
    """
    explicit = [("--xml-dir", _explicit), (f"${ENV_VAR}", os.environ.get(ENV_VAR))]
    for label, value in explicit:
        if value:
            # An explicit setting that is wrong is an error, not a reason to guess elsewhere.
            path = Path(value).expanduser().resolve()
            if (path / "index.xml").is_file():
                return path
            raise DoxygenError(f"No index.xml in {label} -> {path}")

    path = DEFAULT_REL.resolve()
    if (path / "index.xml").is_file():
        return path
    raise DoxygenError(f"No Doxygen XML found at {path}. Pass --xml-dir or set {ENV_VAR}.")


class DoxygenError(Exception):
    """Raised for missing files, wrong compound kinds or malformed XML."""


@lru_cache(maxsize=4)
def _parse_index(path: Path, mtime: float) -> list[tuple[str, str, str]]:
    root = etree.parse(path).getroot()
    return [(c.get("refid"), c.get("kind"), c.findtext("name", default="")) for c in root.findall("compound")]


def list_compounds() -> list[tuple[str, str, str]]:
    """(refid, kind, name) for every compound; re-read when index.xml changes on disk."""
    
    path = get_xml_dir() / "index.xml"
    try:
        return _parse_index(path, path.stat().st_mtime)
    except etree.ParseError as e:
        raise DoxygenError(f"XML parse error in {path}: {e}") from e


Kinds = str | tuple[str, ...] | None


def resolve_refid(ref: str, kind: Kinds = None) -> str:
    """Accept a refid or a (qualified) name and return the refid.

    With `kind`, only compounds of that kind (or any of a tuple of kinds) are
    considered, so a class and a namespace sharing a name don't shadow each other.
    """
    kinds = (kind,) if isinstance(kind, str) else kind
    entries = [e for e in list_compounds() if kinds is None or e[1] in kinds]

    for refid, _, _ in entries:
        if refid == ref:
            return refid
    for refid, _, name in entries:
        if name == ref:
            return refid
    wanted = " or ".join(kinds) if kinds else "compound"
    raise DoxygenError(f"No {wanted} matching '{ref}'")


def load_compounddef(ref: str, kind: str | tuple[str, ...]) -> etree.Element:
    refid = resolve_refid(ref, kind)
    path = get_xml_dir() / f"{refid}.xml"

    if not path.exists():
        raise DoxygenError(f"Could not find XML file for '{refid}'")

    try:
        root = etree.parse(path).getroot()
    except etree.ParseError as e:
        raise DoxygenError(f"XML parse error in {path}: {e}") from e

    cd = root.find("compounddef")
    if cd is None:
        raise DoxygenError(f"Incorrect Doxygen XML structure for '{refid}'")

    return cd


_BLOCK_TAGS = {"para", "listitem", "title", "row", "entry", "term", "simplesect", "programlisting", "codeline"}


def text(el: etree.Element | None) -> str:
    """Flatten an element (description, type, ...) to whitespace-normalised text."""

    if el is None:
        return ""

    parts: list[str] = []

    def walk(node: etree.Element) -> None:
        parts.append(node.text or "")
        for child in node:
            walk(child)
            if child.tag in _BLOCK_TAGS:
                parts.append(" ")  # keep adjacent items ("one", "two") from fusing
            parts.append(child.tail or "")

    walk(el)
    return " ".join("".join(parts).split())


def paragraphs(el: etree.Element | None) -> str:
    """Flatten a description into blocks separated by blank lines.

    Each outermost <para> becomes one block (lists and other nested content stay
    inside it, flattened). <sectN> titles become markdown-style headings.
    """
    if el is None:
        return ""
    blocks: list[str] = []

    def walk(node: etree.Element) -> None:
        for child in node:
            if child.tag == "para":
                blocks.append(text(child))  # do not descend: nested paras are already included
            elif child.tag == "title" and node.tag.startswith("sect"):
                blocks.append("#" * int(node.tag[-1]) + " " + text(child))
            elif child.tag != "title":
                walk(child)

    walk(el)
    return "\n\n".join(b for b in blocks if b)


def location(cd: etree.Element) -> dict:
    loc = cd.find("location")
    if loc is None:
        return {}

    out = {"file": loc.get("file")}
    if loc.get("line"):
        out["line"] = int(loc.get("line"))

    return out


def base_info(cd: etree.Element) -> dict:
    """Fields every compound has."""

    return {
        "refid": cd.get("id"),
        "kind": cd.get("kind"),
        "name": cd.findtext("compoundname", default=""),
        "language": cd.get("language"),
        "brief": text(cd.find("briefdescription")),
        "detailed": paragraphs(cd.find("detaileddescription")),
        "location": location(cd),
    }


def refs(cd: etree.Element, tag: str) -> list[dict]:
    """Collect <innerclass>, <innerfile>, <includes>, ... as {refid, name}."""

    return [{"refid": e.get("refid"), "name": text(e), **({"prot": e.get("prot")} if e.get("prot") else {})}
            for e in cd.findall(tag)]


def members(cd: etree.Element) -> dict[str, list[dict]]:
    """Members grouped by sectiondef kind (public-func, public-attrib, func, var, ...)."""

    out: dict[str, list[dict]] = {}
    for sec in cd.findall("sectiondef"):
        items = [member(m) for m in sec.findall("memberdef")]
        if items:
            out.setdefault(sec.get("kind"), []).extend(items)

    return out


def member(m: etree.Element) -> dict:

    d = {
        "refid": m.get("id"),
        "kind": m.get("kind"),
        "name": m.findtext("name", default=""),
        "prot": m.get("prot"),
        "type": text(m.find("type")),
        "definition": text(m.find("definition")),
        "argsstring": text(m.find("argsstring")),
        "brief": text(m.find("briefdescription")),
        "detailed": paragraphs(m.find("detaileddescription")),
        "location": location(m),
    }

    params = [{"type": text(p.find("type")), "name": text(p.find("declname")) or text(p.find("defname")),
               **({"default": text(p.find("defval"))} if p.find("defval") is not None else {})}
              for p in m.findall("param")]

    if params:
        d["params"] = params
    if m.find("initializer") is not None:
        d["initializer"] = text(m.find("initializer"))

    values = [{"name": v.findtext("name", default=""), "initializer": text(v.find("initializer")),
               "brief": text(v.find("briefdescription"))} for v in m.findall("enumvalue")]
    if values:
        d["enumvalues"] = values

    # Only keep flags that are set, to keep output small
    for flag in ("static", "const", "explicit", "inline", "mutable"):
        if m.get(flag) == "yes":
            d[flag] = True

    if m.get("virt") and m.get("virt") != "non-virtual":
        d["virt"] = m.get("virt")

    return {k: v for k, v in d.items() if v not in ("", None, {}, [])}


def template_params(cd: etree.Element) -> list[dict]:
    
    tpl = cd.find("templateparamlist")
    if tpl is None:
        return []

    return [{"type": text(p.find("type")), **({"default": text(p.find("defval"))} if p.find("defval") is not None else {})}
            for p in tpl.findall("param")]


def prune(d: dict) -> dict:
    """Drop empty values so results stay compact for the LLM."""
    return {k: v for k, v in d.items() if v not in ("", None, {}, [])}
