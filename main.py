import argparse
import sys

from mcp.server import MCPServer

from extractors import *
from extractors.common import *

mcp = MCPServer("moxygen")


def _tool(fn):
    """Register an extractor as an MCP tool, turning errors into {"error": ...}."""
    def wrapper(ref: str) -> dict:
        try:
            return fn(ref)
        except DoxygenError as e:
            return {"error": str(e)}

    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__

    return mcp.tool()(wrapper)


for _fn in (extract_class, extract_struct, extract_namespace, extract_file, extract_dir, extract_page):
    _tool(_fn)


@mcp.tool()
def get_compounds(kind: str | None = None) -> list[dict]:
    """List Doxygen compounds (refid, kind, name), optionally filtered by kind"""

    try:
        return [{"refid": r, "kind": k, "name": n} for r, k, n in _index() if kind is None or k == kind]
    except DoxygenError as e:
        return [{"error": str(e)}]


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP server exposing Doxygen XML documentation.")
    parser.add_argument("--xml-dir", help="Doxygen XML output directory (default: $MOXYGEN_XML_DIR, then ./docs/xml)")
    args = parser.parse_args()
    
    set_xml_dir(args.xml_dir)

    try:
        print(f"moxygen: using {get_xml_dir()}", file=sys.stderr)
    except DoxygenError as e:
        print(f"moxygen: warning: {e}", file=sys.stderr)
    mcp.run()


if __name__ == "__main__":
    main()
