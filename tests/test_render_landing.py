"""Tests for landing page rendering.

Uses tests/samples/test_elements.xsd which has a mix of elements,
complex types, and other definitions to verify the landing template.
"""

import pytest
from conftest import (
    SAMPLES_DIR,
    get_landing,
    get_landing_links,
)

XSD_FILE = SAMPLES_DIR / "test_elements.xsd"


@pytest.fixture(scope="module")
def rendered_html():
    from xsd_browser.main import render_html

    return render_html(XSD_FILE, minify=False)


class TestLandingStructure:
    """The landing page should have sections listing all schema definitions."""

    def test_landing_exists(self, rendered_html):
        assert "<div class=landing>" in rendered_html

    def test_landing_elements_section(self, rendered_html):
        links = get_landing_links(rendered_html, "Elements")
        assert len(links) > 0
        assert "Order" in links

    def test_landing_complex_types_section(self, rendered_html):
        links = get_landing_links(rendered_html, "Complex Types")
        assert "OrderType" in links
        assert "PaymentChoice" in links
        assert "NestedStructure" in links


class TestLandingAbout:
    """The "About" section should show source file name and generator info."""

    def test_landing_about_section(self, rendered_html):
        landing = get_landing(rendered_html)
        assert "About" in landing
        # Source file name should be shown
        assert "test_elements.xsd" in landing

    def test_landing_generator_version(self, rendered_html):
        landing = get_landing(rendered_html)
        assert "xsd-browser" in landing


class TestLandingFooter:
    """Footer should credit xsd-browser and link to TamTam Research."""

    def test_landing_footer(self, rendered_html):
        landing = get_landing(rendered_html)
        assert "xsd-browser" in landing
        assert "tamtamresearch" in landing.lower() or "TamTam" in landing


class TestLandingStats:
    """The stats line should show counts of schema definitions by category."""

    def test_landing_stats(self, rendered_html):
        landing = get_landing(rendered_html)
        assert "elements" in landing.lower()
        assert "complex types" in landing.lower()
