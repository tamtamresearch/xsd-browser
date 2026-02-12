"""Tests for ImportResolver and import-related functions.

Uses minimal XSD files in tests/samples/test_imports/ to verify:
- Namespace prefix assignment for direct and transitive imports
- Duplicate import deduplication
- Prefix collision handling
- Cross-namespace reference rewriting
- XSD prefix normalization (xs: → xsd:)
- Annotation stripping from imported schemas
"""

import lxml.etree
import pytest
from conftest import SAMPLES_DIR

from xsd_browser.main import (
    XSD,
    ImportResolver,
    _normalize_xsd_prefixes,
    xpath,
)

IMPORTS_DIR = SAMPLES_DIR / "test_imports"


@pytest.fixture(scope="module")
def resolved_main():
    """Parse main.xsd and resolve its imports (child_a, child_b, child_c)."""
    main_path = IMPORTS_DIR / "main.xsd"
    doc = lxml.etree.parse(main_path)
    resolver = ImportResolver(doc)
    resolver.handle_imports(doc, main_path)
    return doc, resolver


@pytest.fixture(scope="module")
def resolved_collision():
    """Parse collision.xsd which imports two schemas that both use prefix 'shared'."""
    path = IMPORTS_DIR / "collision.xsd"
    doc = lxml.etree.parse(path)
    resolver = ImportResolver(doc)
    resolver.handle_imports(doc, path)
    return doc, resolver


class TestDirectImports:
    """Imported types should be prefixed with their namespace prefix."""

    def test_direct_import_prefix_a(self, resolved_main):
        doc, resolver = resolved_main
        types = xpath(doc, "//xsd:complexType[@name]")
        type_names = [t.attrib["name"] for t in types]
        assert "a:TypeA" in type_names

    def test_direct_import_prefix_b(self, resolved_main):
        doc, resolver = resolved_main
        types = xpath(doc, "//xsd:complexType[@name]")
        type_names = [t.attrib["name"] for t in types]
        assert "b:TypeB" in type_names

    def test_root_types_unprefixed(self, resolved_main):
        # Root schema's own types keep their original unprefixed names
        doc, resolver = resolved_main
        types = xpath(doc, "//xsd:complexType[@name]")
        type_names = [t.attrib["name"] for t in types]
        assert "MainType" in type_names


class TestTransitiveImports:
    """Imports-of-imports (child_b imports child_c) should be resolved recursively."""

    def test_transitive_import(self, resolved_main):
        doc, resolver = resolved_main
        types = xpath(doc, "//xsd:complexType[@name]")
        type_names = [t.attrib["name"] for t in types]
        assert "c:TypeC" in type_names

    def test_duplicate_import_skipped(self, resolved_main):
        # child_c is only reachable via child_b, so it should appear exactly once
        doc, resolver = resolved_main
        types = xpath(doc, "//xsd:complexType[@name]")
        type_names = [t.attrib["name"] for t in types]
        assert type_names.count("c:TypeC") == 1


class TestPrefixCollision:
    """Both collision_d and collision_e declare xmlns:shared for different namespaces."""

    def test_both_types_imported(self, resolved_collision):
        doc, resolver = resolved_collision
        types = xpath(doc, "//xsd:complexType[@name]")
        type_names = [t.attrib["name"] for t in types]
        assert any("TypeD" in n for n in type_names)
        assert any("TypeE" in n for n in type_names)

    def test_both_namespaces_registered(self, resolved_collision):
        _, resolver = resolved_collision
        assert "http://example.com/d" in resolver.ns_to_prefix
        assert "http://example.com/e" in resolver.ns_to_prefix


class TestDerivePrefix:
    """_derive_prefix_from_ns extracts a short prefix from a namespace URI."""

    def test_derive_prefix_from_ns(self):
        # Takes last path segment, splits on "_", lowercases
        doc = lxml.etree.parse(IMPORTS_DIR / "main.xsd")
        resolver = ImportResolver(doc)
        prefix = resolver._derive_prefix_from_ns("http://example.com/SomeModule_1_2")
        assert prefix == "somemodule"

    def test_derive_prefix_simple(self):
        doc = lxml.etree.parse(IMPORTS_DIR / "main.xsd")
        resolver = ImportResolver(doc)
        prefix = resolver._derive_prefix_from_ns("http://example.com/TEC_3_4")
        assert prefix == "tec"


class TestCrossNamespaceRef:
    """References between imported namespaces should use the global prefix registry."""

    def test_cross_namespace_ref_rewrite(self, resolved_main):
        # child_b's TypeB has an element with type="a:TypeA" (cross-namespace ref)
        doc, resolver = resolved_main
        elems = xpath(
            doc,
            '//xsd:complexType[@name="b:TypeB"]//xsd:element[@name="refToA"]',
        )
        assert len(elems) == 1
        assert elems[0].attrib["type"] == "a:TypeA"


class TestXsdPrefixNormalization:
    """All XSD-namespace prefixes (xs:, xsd:, etc.) should be normalized to xsd:."""

    def test_xsd_prefix_normalized(self):
        schema = lxml.etree.Element(f"{{{XSD}}}schema", nsmap={"xs": XSD})
        el = lxml.etree.SubElement(schema, f"{{{XSD}}}element")
        el.attrib["type"] = "xs:string"
        _normalize_xsd_prefixes(schema, {"xs"})
        assert el.attrib["type"] == "xsd:string"


class TestImportedAnnotationsSkipped:
    """Top-level <xs:annotation> elements from imports should not be merged."""

    def test_imported_annotations_skipped(self, resolved_main):
        doc, resolver = resolved_main
        schema = xpath(doc, "//xsd:schema")[0]
        annotations = xpath(schema, "xsd:annotation")
        assert len(annotations) == 0
