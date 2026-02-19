"""Shared test helpers and fixtures for xsd-browser tests."""

from pathlib import Path

import lxml.html
from lxml import etree

SAMPLES_DIR = Path(__file__).resolve().parent / "samples"


def parse_html(html: str):
    """Parse HTML string into an lxml document."""
    return lxml.html.fromstring(html)


def get_template(doc, data_type: str, path: str):
    """Return the lxml element for a <template> matching data-type + data-path."""
    results = doc.xpath(
        f'//template[@data-type="{data_type}"][@data-path="{path}"]'
    )
    assert results, f"Template not found: data-type={data_type!r} data-path={path!r}"
    return results[0]


def get_element_template(doc, data_type: str, name: str):
    """Return template element by data-name."""
    results = doc.xpath(
        f'//template[@data-type="{data_type}"][@data-name="{name}"]'
    )
    assert results, f"Template not found: data-type={data_type!r} data-name={name!r}"
    return results[0]


def inner_html(elem) -> str:
    """Get inner HTML of an element as string."""
    return (elem.text or '') + ''.join(
        etree.tostring(child, encoding='unicode') for child in elem
    )


def extract_element_names(elem) -> list[str]:
    """Extract element= attribute values from xbe-collapsible-element-ref descendants."""
    return elem.xpath('.//xbe-collapsible-element-ref/@element')


def get_landing(doc):
    """Return the landing div element."""
    results = doc.xpath('//div[@class="landing"]')
    assert results, "Landing section not found"
    return results[0]


def get_landing_section(doc, heading: str):
    """Return the <ul> element following an <h3> with given text."""
    results = doc.xpath(
        f'//div[@class="landing"]//h3[text()="{heading}"]/following-sibling::ul[1]'
    )
    if not results:
        return None
    return results[0]


def get_landing_links(doc, heading: str) -> list[str]:
    """Extract link texts from a landing section."""
    section = get_landing_section(doc, heading)
    if section is None:
        return []
    return [a.text_content() for a in section.xpath('.//a')]
