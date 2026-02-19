"""Tests for element, sequence, choice, and substitution group rendering.

Uses tests/samples/test_elements.xsd which defines:
- OrderType: sequence with various minOccurs/maxOccurs
- PaymentChoice: choice of three payment methods
- NestedStructure: sequence containing a choice
- AbstractShape: abstract element with Circle/Rectangle substitution group
- AnnotatedElement: element with xs:documentation
"""

import pytest
from conftest import (
    SAMPLES_DIR,
    extract_element_names,
    get_element_template,
    get_landing_links,
    get_template,
    inner_html,
    parse_html,
)

XSD_FILE = SAMPLES_DIR / "test_elements.xsd"


@pytest.fixture(scope="module")
def doc():
    from xsd_browser.main import render_html

    html = render_html(XSD_FILE, minify=False)
    return parse_html(html)


class TestSequence:
    """xs:sequence should produce a div.sequence containing all child elements."""

    def test_sequence_class(self, doc):
        tmpl = get_template(doc, "type-contents", "OrderType")
        assert tmpl.xpath('.//div[@class="sequence"]')

    def test_sequence_elements_listed(self, doc):
        tmpl = get_template(doc, "type-contents", "OrderType")
        names = extract_element_names(tmpl)
        assert "orderId" in names
        assert "customer" in names
        assert "note" in names
        assert "item" in names


class TestOccurs:
    """Occurrence badges should appear only for non-default (non-1:1) cardinalities."""

    def test_occurs_optional(self, doc):
        # "note" has minOccurs="0" → should produce a span.occurs
        tmpl = get_template(doc, "type-contents", "OrderType")
        assert tmpl.xpath('.//*[@class="occurs"]')

    def test_occurs_unbounded(self, doc):
        # "item" has maxOccurs="unbounded" → rendered as "*"
        tmpl = get_template(doc, "type-contents", "OrderType")
        content = inner_html(tmpl)
        assert "*" in content

    def test_occurs_default_hidden(self, doc):
        # "orderId" has default 1:1 → no occurs badge near it
        tmpl = get_template(doc, "type-contents", "OrderType")
        order_ids = tmpl.xpath('.//xbe-collapsible-element-ref[@element="orderId"]')
        assert order_ids
        assert not order_ids[0].xpath('.//*[@class="occurs"]')


class TestChoice:
    """xs:choice should produce a div.choice containing all alternative elements."""

    def test_choice_class(self, doc):
        tmpl = get_template(doc, "type-contents", "PaymentChoice")
        assert tmpl.xpath('.//div[@class="choice"]')

    def test_choice_elements_listed(self, doc):
        tmpl = get_template(doc, "type-contents", "PaymentChoice")
        names = extract_element_names(tmpl)
        assert "CreditCard" in names
        assert "BankTransfer" in names
        assert "Cash" in names


class TestNestedChoiceInSequence:
    """A sequence containing a choice should produce both div.sequence and div.choice."""

    def test_nested_choice_in_sequence(self, doc):
        tmpl = get_template(doc, "type-contents", "NestedStructure")
        assert tmpl.xpath('.//div[@class="sequence"]')
        assert tmpl.xpath('.//div[@class="choice"]')


class TestAbstractAndSubstitution:
    """Abstract elements and substitution group members should be annotated properly."""

    def test_abstract_badge(self, doc):
        # abstract="true" → rendered as <span class="small-note">abstract</span>
        tmpl = get_template(doc, "element-head", "AbstractShape")
        content = inner_html(tmpl)
        assert "abstract" in content

    def test_substitution_group_attr(self, doc):
        # Circle's template tag should carry data-substgroup="AbstractShape"
        results = doc.xpath(
            '//template[@data-type="element-head"]'
            '[@data-name="Circle"]'
            '[@data-substgroup="AbstractShape"]'
        )
        assert results


class TestAnnotation:
    """xs:annotation/xs:documentation should be rendered as <p class="annotation">."""

    def test_annotation_rendered(self, doc):
        tmpl = get_template(doc, "element-contents", "AnnotatedElement")
        assert tmpl.xpath('.//*[@class="annotation"]')
        content = inner_html(tmpl)
        assert "This element has important documentation" in content


class TestElementsLanding:
    """Root elements should appear in the landing page's "Elements" section."""

    def test_elements_in_landing(self, doc):
        links = get_landing_links(doc, "Elements")
        assert "Order" in links
        assert "AbstractShape" in links
        assert "AnnotatedElement" in links
