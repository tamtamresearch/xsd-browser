"""Tests for attribute and attribute group rendering.

Uses tests/samples/test_attributes.xsd which defines:
- CommonAttrs: attributeGroup with required "id" and optional "lang"
- StyledElement: complexType using CommonAttrs + own "style" attribute
- FixedAttr: complexType with a fixed-value "version" attribute
"""

import re

import pytest
from conftest import SAMPLES_DIR, get_template

XSD_FILE = SAMPLES_DIR / "test_attributes.xsd"


@pytest.fixture(scope="module")
def rendered_html():
    from xsd_browser.main import render_html

    return render_html(XSD_FILE, minify=False)


class TestAttributes:
    """Individual attribute rendering: required badge, type links."""

    def test_required_attribute_badge(self, rendered_html):
        # "id" has use="required" → should show a "required" badge
        content = get_template(
            rendered_html,
            "attribute-group",
            "CommonAttrs",
        )
        assert "required" in content

    def test_optional_attribute_no_required_badge(self, rendered_html):
        # "lang" has no use attribute (defaults to optional) → no "required" badge
        content = get_template(
            rendered_html,
            "attribute-group",
            "CommonAttrs",
        )
        parts = re.split(r"<span class=attribute", content)
        lang_part = [p for p in parts if "lang=" in p]
        assert len(lang_part) >= 1
        assert "required" not in lang_part[0] or "lang" not in lang_part[0].split("required")[0]

    def test_attribute_type_link(self, rendered_html):
        # Attribute types should be rendered as clickable type links
        content = get_template(
            rendered_html,
            "attribute-group",
            "CommonAttrs",
        )
        assert 'class="type-link' in content


class TestAttributeGroup:
    """Attribute groups should be defined as templates and referenced via <xbe-ref>."""

    def test_attribute_group_defined(self, rendered_html):
        # A <template data-type="attribute-group"> should exist for CommonAttrs
        assert 'data-type="attribute-group"' in rendered_html
        content = get_template(
            rendered_html,
            "attribute-group",
            "CommonAttrs",
        )
        assert content

    def test_attribute_group_referenced(self, rendered_html):
        # StyledElement's type-attrs should contain an <xbe-ref> to CommonAttrs
        content = get_template(
            rendered_html,
            "type-attrs",
            "StyledElement",
        )
        assert "type=attribute-group" in content or 'type="attribute-group"' in content
        assert "CommonAttrs" in content

    def test_own_attribute_shown(self, rendered_html):
        # StyledElement also declares its own "style" attribute directly
        content = get_template(
            rendered_html,
            "type-attrs",
            "StyledElement",
        )
        assert "style=" in content


class TestAttributeGroupsLanding:
    """Attribute groups are not listed on the landing page, but their templates should exist."""

    def test_attribute_groups_in_landing(self, rendered_html):
        assert 'data-type="attribute-group"' in rendered_html
