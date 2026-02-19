"""Tests for simple type rendering (enums, facets, unions, lists, patterns).

Uses tests/samples/test_simple_types.xsd which defines:
- ColorEnum: restriction with enumerations (one documented)
- StatusCode: restriction with minInclusive/maxInclusive
- MixedUnion: union of xs:date and xs:dateTime
- TokenList: list of xs:token
- SizeType: restriction with pattern facet
"""

import pytest
from conftest import (
    SAMPLES_DIR,
    get_landing_links,
    get_template,
    inner_html,
    parse_html,
)

XSD_FILE = SAMPLES_DIR / "test_simple_types.xsd"


@pytest.fixture(scope="module")
def doc():
    from xsd_browser.main import render_html

    html = render_html(XSD_FILE, minify=False)
    return parse_html(html)


class TestEnumeration:
    """Enum values should be rendered as <code> elements inside a restriction block."""

    def test_enum_values_rendered(self, doc):
        tmpl = get_template(doc, "type-contents", "ColorEnum")
        codes = [c.text for c in tmpl.xpath('.//code')]
        assert "Red" in codes
        assert "Green" in codes
        assert "Blue" in codes

    def test_enum_documentation(self, doc):
        # "Red" has an xs:documentation child → rendered as span.enum-doc
        tmpl = get_template(doc, "type-contents", "ColorEnum")
        assert tmpl.xpath('.//*[@class="enum-doc"]')
        content = inner_html(tmpl)
        assert "The color red" in content

    def test_restriction_base_shown(self, doc):
        # The restriction's base type (xsd:string) should be linked
        tmpl = get_template(doc, "type-contents", "ColorEnum")
        content = inner_html(tmpl)
        assert "xsd:string" in content


class TestFacets:
    """Numeric and pattern facets should be rendered as pretty-printed XML."""

    def test_facets_rendered(self, doc):
        # StatusCode has minInclusive=100 and maxInclusive=599
        tmpl = get_template(doc, "type-contents", "StatusCode")
        content = inner_html(tmpl)
        assert "100" in content
        assert "599" in content

    def test_pattern_facet_rendered(self, doc):
        # SizeType has a regex pattern
        tmpl = get_template(doc, "type-contents", "SizeType")
        content = inner_html(tmpl)
        assert "[SML]|X{1,3}L" in content


class TestUnion:
    """Union types should show member types and use the simple-union CSS class."""

    def test_union_members_shown(self, doc):
        tmpl = get_template(doc, "type-contents", "MixedUnion")
        content = inner_html(tmpl)
        # memberTypes values keep original xs: prefix (not normalized to xsd:)
        assert "xs:date" in content
        assert "xs:dateTime" in content

    def test_union_css_class(self, doc):
        tmpl = get_template(doc, "type-contents", "MixedUnion")
        assert tmpl.xpath('.//*[@class="simple-union"]')


class TestList:
    """List types should show item type and use the simple-list CSS class."""

    def test_list_item_type_shown(self, doc):
        tmpl = get_template(doc, "type-contents", "TokenList")
        content = inner_html(tmpl)
        # itemType keeps original xs: prefix (not normalized to xsd:)
        assert "xs:token" in content

    def test_list_css_class(self, doc):
        tmpl = get_template(doc, "type-contents", "TokenList")
        assert tmpl.xpath('.//*[@class="simple-list"]')


class TestSimpleTypeLanding:
    """All 5 simple types should appear in the landing page's "Simple Types" section."""

    def test_simple_type_in_landing(self, doc):
        links = get_landing_links(doc, "Simple Types")
        assert "ColorEnum" in links
        assert "StatusCode" in links
        assert "MixedUnion" in links
        assert "TokenList" in links
        assert "SizeType" in links
