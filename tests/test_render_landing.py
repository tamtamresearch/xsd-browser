"""Tests for landing page rendering.

Uses tests/samples/test_elements.xsd which has a mix of elements,
complex types, and other definitions to verify the landing template.
"""

import pytest
from conftest import (
    SAMPLES_DIR,
    get_landing,
    get_landing_links,
    inner_html,
    parse_html,
)

XSD_FILE = SAMPLES_DIR / "test_elements.xsd"


@pytest.fixture(scope="module")
def doc():
    from xsd_browser.main import render_html

    html = render_html(XSD_FILE, minify=False)
    return parse_html(html)


class TestLandingStructure:
    """The landing page should have sections listing all schema definitions."""

    def test_landing_exists(self, doc):
        assert doc.xpath('//div[@class="landing"]')

    def test_landing_elements_section(self, doc):
        links = get_landing_links(doc, "Elements")
        assert len(links) > 0
        assert "Order" in links

    def test_landing_complex_types_section(self, doc):
        links = get_landing_links(doc, "Complex Types")
        assert "OrderType" in links
        assert "PaymentChoice" in links
        assert "NestedStructure" in links


class TestLandingAbout:
    """The "About" section should show source file name and generator info."""

    def test_landing_about_section(self, doc):
        landing = get_landing(doc)
        text = inner_html(landing)
        assert "About" in text
        # Source file name should be shown
        assert "test_elements.xsd" in text

    def test_landing_generator_version(self, doc):
        landing = get_landing(doc)
        text = inner_html(landing)
        assert "xsd-browser" in text


class TestLandingFooter:
    """Footer should credit xsd-browser and link to TamTam Research."""

    def test_landing_footer(self, doc):
        landing = get_landing(doc)
        text = inner_html(landing)
        assert "xsd-browser" in text
        assert "tamtamresearch" in text.lower() or "TamTam" in text


class TestLandingStats:
    """The stats line should show counts of schema definitions by category."""

    def test_landing_stats(self, doc):
        landing = get_landing(doc)
        text = inner_html(landing)
        assert "elements" in text.lower()
        assert "complex types" in text.lower()
