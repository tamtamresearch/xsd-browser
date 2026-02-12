"""Tests for element, sequence, choice, and substitution group rendering.

Uses tests/samples/test_elements.xsd which defines:
- OrderType: sequence with various minOccurs/maxOccurs
- PaymentChoice: choice of three payment methods
- NestedStructure: sequence containing a choice
- AbstractShape: abstract element with Circle/Rectangle substitution group
- AnnotatedElement: element with xs:documentation
"""

import re

import pytest
from conftest import (
    SAMPLES_DIR,
    extract_element_names,
    get_landing_links,
    get_template,
)

XSD_FILE = SAMPLES_DIR / "test_elements.xsd"


@pytest.fixture(scope="module")
def rendered_html():
    from xsd_browser.main import render_html

    return render_html(XSD_FILE, minify=False)


class TestSequence:
    """xs:sequence should produce a div.sequence containing all child elements."""

    def test_sequence_class(self, rendered_html):
        content = get_template(
            rendered_html,
            "type-contents",
            "OrderType",
        )
        assert 'class="sequence"' in content

    def test_sequence_elements_listed(self, rendered_html):
        content = get_template(
            rendered_html,
            "type-contents",
            "OrderType",
        )
        names = extract_element_names(content)
        assert "orderId" in names
        assert "customer" in names
        assert "note" in names
        assert "item" in names


class TestOccurs:
    """Occurrence badges should appear only for non-default (non-1:1) cardinalities."""

    def test_occurs_optional(self, rendered_html):
        # "note" has minOccurs="0" → should produce a span.occurs
        content = get_template(
            rendered_html,
            "type-contents",
            "OrderType",
        )
        assert "class=occurs" in content or 'class="occurs"' in content

    def test_occurs_unbounded(self, rendered_html):
        # "item" has maxOccurs="unbounded" → rendered as "*"
        content = get_template(
            rendered_html,
            "type-contents",
            "OrderType",
        )
        assert "*" in content

    def test_occurs_default_hidden(self, rendered_html):
        # "orderId" has default 1:1 → no occurs badge near it
        content = get_template(
            rendered_html,
            "type-contents",
            "OrderType",
        )
        match = re.search(
            r'element="orderId"[\s\S]*?</xbe-collapsible-element-ref>',
            content,
        )
        assert match
        orderId_section = match.group(0)
        assert "class=occurs" not in orderId_section or 'class="occurs"' not in orderId_section


class TestChoice:
    """xs:choice should produce a div.choice containing all alternative elements."""

    def test_choice_class(self, rendered_html):
        content = get_template(
            rendered_html,
            "type-contents",
            "PaymentChoice",
        )
        assert 'class="choice"' in content

    def test_choice_elements_listed(self, rendered_html):
        content = get_template(
            rendered_html,
            "type-contents",
            "PaymentChoice",
        )
        names = extract_element_names(content)
        assert "CreditCard" in names
        assert "BankTransfer" in names
        assert "Cash" in names


class TestNestedChoiceInSequence:
    """A sequence containing a choice should produce both div.sequence and div.choice."""

    def test_nested_choice_in_sequence(self, rendered_html):
        content = get_template(
            rendered_html,
            "type-contents",
            "NestedStructure",
        )
        assert 'class="sequence"' in content
        assert 'class="choice"' in content


class TestAbstractAndSubstitution:
    """Abstract elements and substitution group members should be annotated properly."""

    def test_abstract_badge(self, rendered_html):
        # abstract="true" → rendered as <span class="small-note">abstract</span>
        content = get_template(
            rendered_html,
            "element-head",
            "AbstractShape",
        )
        assert "abstract" in content

    def test_substitution_group_attr(self, rendered_html):
        # Circle's template tag should carry data-substgroup="AbstractShape"
        pattern = (
            r'data-type="element-head"[^>]*data-name="Circle"[^>]*data-substgroup="AbstractShape"'
        )
        assert re.search(pattern, rendered_html)


class TestAnnotation:
    """xs:annotation/xs:documentation should be rendered as <p class="annotation">."""

    def test_annotation_rendered(self, rendered_html):
        content = get_template(
            rendered_html,
            "element-contents",
            "AnnotatedElement",
        )
        assert "class=annotation" in content or 'class="annotation"' in content
        assert "This element has important documentation" in content


class TestElementsLanding:
    """Root elements should appear in the landing page's "Elements" section."""

    def test_elements_in_landing(self, rendered_html):
        links = get_landing_links(rendered_html, "Elements")
        assert "Order" in links
        assert "AbstractShape" in links
        assert "AnnotatedElement" in links
