"""Tests for usages and "Extended by" rendering.

Uses tests/samples/inherited_elements_demo.xsd which has extension chains:
- AnimalBase → Dog → ServiceDog (extension chain)

All types/elements are prefixed with "tns:" due to the schema's targetNamespace.
"""

import pytest
from conftest import SAMPLES_DIR, get_template

INHERITED_XSD = SAMPLES_DIR / "inherited_elements_demo.xsd"
NS = "tns:"


@pytest.fixture(scope="module")
def rendered_html():
    from xsd_browser.main import render_html

    return render_html(INHERITED_XSD, minify=False)


class TestExtendedBy:
    """Types that are extended should show an "Extended by" box listing derived types."""

    def test_extended_by_section(self, rendered_html):
        # AnimalBase is extended by Dog → should have an extended-by-box
        content = get_template(
            rendered_html,
            "type-contents",
            NS + "AnimalBase",
        )
        assert 'class="extended-by-box"' in content

    def test_extended_by_lists_derived_types(self, rendered_html):
        content = get_template(
            rendered_html,
            "type-contents",
            NS + "AnimalBase",
        )
        assert NS + "Dog" in content

    def test_extended_by_absent_for_leaf(self, rendered_html):
        # ServiceDog has no derived types → no extended-by-box
        content = get_template(
            rendered_html,
            "type-contents",
            NS + "ServiceDog",
        )
        assert "extended-by-box" not in content


class TestUsages:
    """Every named definition should have a *-usages template tracking where it's used."""

    def test_type_usages_template_exists(self, rendered_html):
        # AnimalBase is referenced by Dog (extension) and Animal element (type attr)
        content = get_template(
            rendered_html,
            "type-usages",
            NS + "AnimalBase",
        )
        assert content

    def test_element_usages_template_exists(self, rendered_html):
        # Top-level elements also get usages templates (prefixed with tns:)
        content = get_template(
            rendered_html,
            "element-usages",
            NS + "Dog",
        )
        assert content

    def test_type_usages_lists_users(self, rendered_html):
        # AnimalBase should list Dog (extends it) and/or Animal (uses it as type)
        content = get_template(
            rendered_html,
            "type-usages",
            NS + "AnimalBase",
        )
        assert "Dog" in content or "Animal" in content
