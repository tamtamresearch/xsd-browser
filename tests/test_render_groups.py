"""Tests for named group rendering.

Uses tests/samples/test_groups.xsd which defines:
- AddressGroup: named group with sequence (street, city, zip)
- PersonType: complexType referencing AddressGroup
- NestedGroupType: complexType with group ref alongside own elements
"""

import pytest
from conftest import (
    SAMPLES_DIR,
    extract_element_names,
    get_landing_links,
    get_template,
    inner_html,
    parse_html,
)

XSD_FILE = SAMPLES_DIR / "test_groups.xsd"


@pytest.fixture(scope="module")
def doc():
    from xsd_browser.main import render_html

    html = render_html(XSD_FILE, minify=False)
    return parse_html(html)


class TestGroupDefinition:
    """Named groups should produce a group-contents template with their child elements."""

    def test_group_template_exists(self, doc):
        tmpl = get_template(doc, "group-contents", "AddressGroup")
        assert tmpl is not None

    def test_group_elements(self, doc):
        # All elements defined in the group's sequence should be present
        tmpl = get_template(doc, "group-contents", "AddressGroup")
        names = extract_element_names(tmpl)
        assert "street" in names
        assert "city" in names
        assert "zip" in names


class TestGroupReference:
    """Types that reference a group via <xs:group ref="..."> should emit an <xbe-ref>."""

    def test_group_ref_in_type(self, doc):
        # PersonType references AddressGroup → should contain an xbe-ref to group-contents
        tmpl = get_template(doc, "type-contents", "PersonType")
        refs = tmpl.xpath('.//xbe-ref[@type="group-contents"]')
        assert refs
        content = inner_html(tmpl)
        assert "AddressGroup" in content

    def test_group_alongside_own_elements(self, doc):
        # NestedGroupType has own elements (companyName, phone) AND a group ref
        tmpl = get_template(doc, "type-contents", "NestedGroupType")
        names = extract_element_names(tmpl)
        assert "companyName" in names
        assert "phone" in names
        content = inner_html(tmpl)
        assert "AddressGroup" in content


class TestGroupsLanding:
    """Named groups should appear in the landing page's "Groups" section."""

    def test_groups_in_landing(self, doc):
        links = get_landing_links(doc, "Groups")
        assert "AddressGroup" in links
