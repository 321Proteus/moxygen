# moxygen
A simple MCP that allows AI to read Doxygen XML docs.

## Setup

```sh
python -m venv venv
venv/bin/pip install -e '.[dev]'    # installs mcp>=2.3,<3 (+ pytest)
venv/bin/pytest     # tests run against tests/fixtures/xml
```

## Usage

Generate Doxygen with `GENERATE_XML = YES`, then register the server in the project that owns the docs (`.mcp.json` at its root):

```json
{
  "mcpServers": {
    "moxygen": {
      "command": "/path/to/moxygen/venv/bin/python",
      "args": ["/path/to/moxygen/main.py", "--xml-dir", "build/docs/xml"]
    }
  }
}
```

Or: `claude mcp add moxygen -- /path/to/moxygen/venv/bin/python /path/to/moxygen/main.py`

The XML directory is resolved as `--xml-dir`, then `$MOXYGEN_XML_DIR`, then `./docs/xml` in the
directory the server is launched from. Relative paths are relative to that directory.
Changes to `index.xml` are picked up without a restart.

### Tools
 - `get_compounds`
 - `extract_class`
 - `extract_struct`
 - `extract_namespace`
 - `extract_file`,
 - `extract_dir`
 - `extract_page`

Each one takes a refid or a name.
