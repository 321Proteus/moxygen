import pytest

from extractors import (extract_class, extract_dir, extract_file,
                        extract_namespace, extract_page, extract_struct)
from extractors.common import DoxygenError, list_compounds, paragraphs, set_xml_dir, get_xml_dir
import xml.etree.ElementTree as etree


def test_class_and_namespace_sharing_a_name_both_resolve():
    # The namespace is listed first in index.xml; the class must still be found.
    assert extract_class("demo::Config")["kind"] == "class"
    assert extract_namespace("demo::Config")["kind"] == "namespace"


def test_wrong_kind_by_refid_is_an_error():
    with pytest.raises(DoxygenError, match="No struct matching"):
        extract_struct("ab/classdemo_1_1Config")


def test_class_details():
    c = extract_class("demo::Config")
    assert c["brief"] == "Runtime configuration."
    assert c["detailed"] == "First paragraph.\n\nSecond paragraph."
    assert c["template_params"] == [{"type": "typename T", "default": "int"}]
    assert c["bases"][0]["name"] == "demo::Point"
    load = c["members"]["public-func"][0]
    assert load["name"] == "load" and load["static"] is True
    assert load["params"][1] == {"type": "int", "name": "flags", "default": "0"}


def test_struct_members_and_derived():
    s = extract_struct("demo::Point")
    assert s["derived"][0]["name"] == "demo::Config"
    assert s["members"]["public-attrib"][0]["initializer"] == "= 0"


def test_namespace_file_dir():
    assert extract_namespace("demo::Config")["inner_classes"][0]["name"] == "demo::Point"
    f = extract_file("util.hpp")
    assert f["includes"][0]["name"] == "vector" and "programlisting" not in str(f)
    d = extract_dir("src/demo")
    assert d["files"][0]["name"] == "util.hpp" and d["subdirs"][0]["name"] == "sub"


def test_page_nested_lists_and_sections():
    p = extract_page("index")
    assert p["title"] == "Demo"
    assert [s["title"] for s in p["sections"]] == ["Features", "Details"]
    assert p["content"] == ("Intro text.\n\n# Features\n\n"
                            "Outer para: one two\n\n## Details\n\nDeep text.")


def test_paragraphs_does_not_duplicate_nested_paras():
    el = etree.fromstring("<d><para>a <itemizedlist><listitem><para>b</para></listitem></itemizedlist></para></d>")
    assert paragraphs(el) == "a b"
    assert paragraphs(None) == ""


def test_unknown_ref():
    with pytest.raises(DoxygenError):
        extract_class("nope")


def test_xml_dir_precedence(tmp_path, monkeypatch, xml_dir):
    monkeypatch.setenv("MOXYGEN_XML_DIR", str(tmp_path))  # env set but invalid
    set_xml_dir(None)
    with pytest.raises(DoxygenError, match="MOXYGEN_XML_DIR"):
        get_xml_dir()
    set_xml_dir(xml_dir)  # --xml-dir wins over the env var
    assert get_xml_dir() == xml_dir.resolve()


def test_default_dir_is_relative_to_cwd(tmp_path, monkeypatch, xml_dir):
    set_xml_dir(None)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(DoxygenError, match="No Doxygen XML found"):
        get_xml_dir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "xml").symlink_to(xml_dir)
    assert (get_xml_dir() / "index.xml").is_file()


def test_index_reloads_when_changed(tmp_path):
    (tmp_path / "index.xml").write_text('<doxygenindex><compound refid="a" kind="page"><name>a</name></compound></doxygenindex>')
    set_xml_dir(tmp_path)
    assert [c[2] for c in list_compounds()] == ["a"]
    import os
    p = tmp_path / "index.xml"
    p.write_text('<doxygenindex><compound refid="b" kind="page"><name>b</name></compound></doxygenindex>')
    os.utime(p, (p.stat().st_atime, p.stat().st_mtime + 5))
    assert [c[2] for c in list_compounds()] == ["b"]
