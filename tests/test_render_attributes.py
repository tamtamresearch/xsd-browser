"""Tests for attribute and attribute group rendering.

Uses tests/samples/test_attributes.xsd which defines:
- CommonAttrs: attributeGroup with required "id" and optional "lang"
- StyledElement: complexType using CommonAttrs + own "style" attribute
- FixedAttr: complexType with a fixed-value "version" attribute
"""

import pytest
from conftest import SAMPLES_DIR, get_template, inner_html, parse_html

XSD_FILE = SAMPLES_DIR / "test_attributes.xsd"


@pytest.fixture(scope="module")
def doc():
    from xsd_browser.main import render_html

    html = render_html(XSD_FILE, minify=False)
    return parse_html(html)


class TestAttributes:
    """Individual attribute rendering: required badge, type links."""

    def test_required_attribute_badge(self, doc):
        # "id" has use="required" → should show a "required" badge
        tmpl = get_template(doc, "attribute-group", "CommonAttrs")
        content = inner_html(tmpl)
        assert "required" in content

    def test_optional_attribute_no_required_badge(self, doc):
        # "lang" has no use attribute (defaults to optional) → no "required" badge
        tmpl = get_template(doc, "attribute-group", "CommonAttrs")
        attrs = tmpl.xpath('.//*[@class="attribute"]')
        for attr in attrs:
            content = inner_html(attr)
            if "lang=" in content:
                assert "required" not in content
                break
        else:
            pytest.fail("lang attribute not found")

    def test_attribute_type_link(self, doc):
        # Attribute types should be rendered as clickable type links
        tmpl = get_template(doc, "attribute-group", "CommonAttrs")
        assert tmpl.xpath('.//*[contains(@class, "type-link")]')


class TestAttributeGroup:
    """Attribute groups should be defined as templates and referenced via <xbe-ref>."""

    def test_attribute_group_defined(self, doc):
        # A <template data-type="attribute-group"> should exist for CommonAttrs
        assert doc.xpath('//template[@data-type="attribute-group"]')
        tmpl = get_template(doc, "attribute-group", "CommonAttrs")
        assert tmpl is not None

    def test_attribute_group_referenced(self, doc):
        # StyledElement's type-attrs should contain an <xbe-ref> to CommonAttrs
        tmpl = get_template(doc, "type-attrs", "StyledElement")
        refs = tmpl.xpath('.//xbe-ref[@type="attribute-group"]')
        assert refs
        content = inner_html(tmpl)
        assert "CommonAttrs" in content

    def test_own_attribute_shown(self, doc):
        # StyledElement also declares its own "style" attribute directly
        tmpl = get_template(doc, "type-attrs", "StyledElement")
        content = inner_html(tmpl)
        assert "style=" in content


class TestAttributeGroupsLanding:
    """Attribute groups are not listed on the landing page, but their templates should exist."""

    def test_attribute_groups_in_landing(self, doc):
        assert doc.xpath('//template[@data-type="attribute-group"]')
