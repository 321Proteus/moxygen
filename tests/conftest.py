from pathlib import Path

import pytest

from extractors.common import list_compounds, set_xml_dir

FIXTURE = Path(__file__).parent / "fixtures" / "xml"


@pytest.fixture(autouse=True)
def xml_dir(monkeypatch):
    monkeypatch.delenv("MOXYGEN_XML_DIR", raising=False)
    set_xml_dir(FIXTURE)
    yield FIXTURE
    set_xml_dir(None)
