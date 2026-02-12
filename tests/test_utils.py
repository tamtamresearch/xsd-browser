"""Unit tests for utility functions in xsd_browser.main.

Tests the pure functions that operate on lxml elements directly,
without rendering through the Jinja2 template. Each function is
tested with hand-built XSD element trees.
"""

import lxml.etree

from xsd_browser.main import (
    XSD,
    _normalize_xsd_prefixes,
    elem_name_attrs,
    elem_path,
    elem_path_attrs,
    elem_type,
    prettyprint_xml,
    xpath,
    xpath_one,
)


def _make_element(local_name, name=None, parent=None):
    """Create an XSD-namespaced element with optional name attribute and parent."""
    tag = f"{{{XSD}}}{local_name}"
    el = lxml.etree.SubElement(parent, tag) if parent is not None else lxml.etree.Element(tag)
    if name:
        el.attrib["name"] = name
    return el


# --- elem_type: maps XSD tag → category string used in data-type attributes ---


def test_elem_type_element():
    el = _make_element("element")
    assert elem_type(el) == "element"


def test_elem_type_complex():
    # Both complexType and simpleType map to "type"
    el = _make_element("complexType")
    assert elem_type(el) == "type"


def test_elem_type_simple():
    el = _make_element("simpleType")
    assert elem_type(el) == "type"


def test_elem_type_group():
    el = _make_element("group")
    assert elem_type(el) == "group"


def test_elem_type_attribute_group():
    # attributeGroup uses a hyphenated category
    el = _make_element("attributeGroup")
    assert elem_type(el) == "attribute-group"


# --- elem_path: walks up the tree collecting @name values ---


def test_elem_path_root():
    # Single element with no parent → path is just [name]
    el = _make_element("element", name="root")
    assert elem_path(el) == ["root"]


def test_elem_path_nested():
    # Path is leaf-first: [child, parent, root]
    root = _make_element("schema", name="root")
    parent = _make_element("complexType", name="parent", parent=root)
    child = _make_element("element", name="child", parent=parent)
    assert elem_path(child) == [
        "child",
        "parent",
        "root",
    ]


# --- elem_path_attrs: generates HTML data-* attributes for template matching ---


def test_elem_path_attrs():
    root = _make_element("schema", name="root")
    child = _make_element("element", name="child", parent=root)
    attrs = elem_path_attrs(child)
    assert attrs["data-name"] == "child"
    # Path is joined with "/"
    assert attrs["data-path"] == "child/root"
    # No substitutionGroup → empty string
    assert attrs["data-substgroup"] == ""


def test_elem_path_attrs_with_substgroup():
    # substitutionGroup attribute is forwarded to data-substgroup
    el = _make_element("element", name="Circle")
    el.attrib["substitutionGroup"] = "AbstractShape"
    attrs = elem_path_attrs(el)
    assert attrs["data-substgroup"] == "AbstractShape"


# --- elem_name_attrs: generates data-name and optional data-belowroot ---


def test_elem_name_attrs_belowroot():
    # Direct child of <xs:schema> gets data-belowroot=True
    schema = _make_element("schema", name="myschema")
    child = _make_element("element", name="MyElem", parent=schema)
    attrs = elem_name_attrs(child)
    assert attrs["data-name"] == "MyElem"
    assert attrs["data-belowroot"] is True


def test_elem_name_attrs_nested():
    # Element nested inside a complexType does NOT get data-belowroot
    schema = _make_element("schema")
    ct = _make_element("complexType", parent=schema)
    child = _make_element("element", name="nested", parent=ct)
    attrs = elem_name_attrs(child)
    assert attrs["data-name"] == "nested"
    assert "data-belowroot" not in attrs


# --- prettyprint_xml: strips namespace URIs and pretty-prints ---


def test_prettyprint_xml():
    el = lxml.etree.Element(f"{{{XSD}}}element")
    el.attrib["name"] = "test"
    result = prettyprint_xml(el)
    # Tag should appear as local name only
    assert "element" in result
    assert 'name="test"' in result
    # Full namespace URI must be stripped
    assert "http://www.w3.org/2001/XMLSchema" not in result


# --- xpath / xpath_one: XSD-aware XPath helpers ---


def test_xpath_returns_list():
    # xpath() always returns a list
    schema = lxml.etree.Element(f"{{{XSD}}}schema")
    _make_element("element", name="a", parent=schema)
    _make_element("element", name="b", parent=schema)
    results = xpath(schema, "xsd:element")
    assert len(results) == 2


def test_xpath_one_found():
    # xpath_one() returns the single matching element
    schema = lxml.etree.Element(f"{{{XSD}}}schema")
    _make_element("element", name="a", parent=schema)
    result = xpath_one(schema, 'xsd:element[@name="a"]')
    assert result is not None
    assert result.attrib["name"] == "a"


def test_xpath_one_not_found():
    # xpath_one() returns None when nothing matches
    schema = lxml.etree.Element(f"{{{XSD}}}schema")
    result = xpath_one(schema, 'xsd:element[@name="missing"]')
    assert result is None


# --- _normalize_xsd_prefixes: rewrites xs:→xsd: in @type/@base ---


def test_normalize_xsd_prefixes():
    # "xs:string" should become "xsd:string"
    schema = lxml.etree.Element(f"{{{XSD}}}schema", nsmap={"xs": XSD})
    el = _make_element("element", parent=schema)
    el.attrib["type"] = "xs:string"
    _normalize_xsd_prefixes(schema, {"xs"})
    assert el.attrib["type"] == "xsd:string"


def test_normalize_xsd_prefixes_leaves_xsd_alone():
    # Already canonical "xsd:" prefix should not be changed
    schema = lxml.etree.Element(f"{{{XSD}}}schema", nsmap={"xsd": XSD})
    el = _make_element("element", parent=schema)
    el.attrib["type"] = "xsd:integer"
    _normalize_xsd_prefixes(schema, {"xsd"})
    assert el.attrib["type"] == "xsd:integer"
