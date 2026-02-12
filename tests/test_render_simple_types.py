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
)

XSD_FILE = SAMPLES_DIR / "test_simple_types.xsd"


@pytest.fixture(scope="module")
def rendered_html():
    from xsd_browser.main import render_html

    return render_html(XSD_FILE, minify=False)


class TestEnumeration:
    """Enum values should be rendered as <code> elements inside a restriction block."""

    def test_enum_values_rendered(self, rendered_html):
        content = get_template(
            rendered_html,
            "type-contents",
            "ColorEnum",
        )
        assert "<code>Red</code>" in content
        assert "<code>Green</code>" in content
        assert "<code>Blue</code>" in content

    def test_enum_documentation(self, rendered_html):
        # "Red" has an xs:documentation child → rendered as span.enum-doc
        content = get_template(
            rendered_html,
            "type-contents",
            "ColorEnum",
        )
        assert 'class="enum-doc"' in content
        assert "The color red" in content

    def test_restriction_base_shown(self, rendered_html):
        # The restriction's base type (xsd:string) should be linked
        content = get_template(
            rendered_html,
            "type-contents",
            "ColorEnum",
        )
        assert "xsd:string" in content


class TestFacets:
    """Numeric and pattern facets should be rendered as pretty-printed XML."""

    def test_facets_rendered(self, rendered_html):
        # StatusCode has minInclusive=100 and maxInclusive=599
        content = get_template(
            rendered_html,
            "type-contents",
            "StatusCode",
        )
        assert "100" in content
        assert "599" in content

    def test_pattern_facet_rendered(self, rendered_html):
        # SizeType has a regex pattern
        content = get_template(
            rendered_html,
            "type-contents",
            "SizeType",
        )
        assert "[SML]|X{1,3}L" in content


class TestUnion:
    """Union types should show member types and use the simple-union CSS class."""

    def test_union_members_shown(self, rendered_html):
        content = get_template(
            rendered_html,
            "type-contents",
            "MixedUnion",
        )
        # memberTypes values keep original xs: prefix (not normalized to xsd:)
        assert "xs:date" in content
        assert "xs:dateTime" in content

    def test_union_css_class(self, rendered_html):
        content = get_template(
            rendered_html,
            "type-contents",
            "MixedUnion",
        )
        assert 'class="simple-union"' in content


class TestList:
    """List types should show item type and use the simple-list CSS class."""

    def test_list_item_type_shown(self, rendered_html):
        content = get_template(
            rendered_html,
            "type-contents",
            "TokenList",
        )
        # itemType keeps original xs: prefix (not normalized to xsd:)
        assert "xs:token" in content

    def test_list_css_class(self, rendered_html):
        content = get_template(
            rendered_html,
            "type-contents",
            "TokenList",
        )
        assert 'class="simple-list"' in content


class TestSimpleTypeLanding:
    """All 5 simple types should appear in the landing page's "Simple Types" section."""

    def test_simple_type_in_landing(self, rendered_html):
        links = get_landing_links(rendered_html, "Simple Types")
        assert "ColorEnum" in links
        assert "StatusCode" in links
        assert "MixedUnion" in links
        assert "TokenList" in links
        assert "SizeType" in links
