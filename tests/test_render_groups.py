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
)

XSD_FILE = SAMPLES_DIR / "test_groups.xsd"


@pytest.fixture(scope="module")
def rendered_html():
    from xsd_browser.main import render_html

    return render_html(XSD_FILE, minify=False)


class TestGroupDefinition:
    """Named groups should produce a group-contents template with their child elements."""

    def test_group_template_exists(self, rendered_html):
        content = get_template(
            rendered_html,
            "group-contents",
            "AddressGroup",
        )
        assert content

    def test_group_elements(self, rendered_html):
        # All elements defined in the group's sequence should be present
        content = get_template(
            rendered_html,
            "group-contents",
            "AddressGroup",
        )
        names = extract_element_names(content)
        assert "street" in names
        assert "city" in names
        assert "zip" in names


class TestGroupReference:
    """Types that reference a group via <xs:group ref="..."> should emit an <xbe-ref>."""

    def test_group_ref_in_type(self, rendered_html):
        # PersonType references AddressGroup → should contain an xbe-ref to group-contents
        content = get_template(
            rendered_html,
            "type-contents",
            "PersonType",
        )
        assert "type=group-contents" in content or 'type="group-contents"' in content
        assert "AddressGroup" in content

    def test_group_alongside_own_elements(self, rendered_html):
        # NestedGroupType has own elements (companyName, phone) AND a group ref
        content = get_template(
            rendered_html,
            "type-contents",
            "NestedGroupType",
        )
        names = extract_element_names(content)
        assert "companyName" in names
        assert "phone" in names
        assert "AddressGroup" in content


class TestGroupsLanding:
    """Named groups should appear in the landing page's "Groups" section."""

    def test_groups_in_landing(self, rendered_html):
        links = get_landing_links(rendered_html, "Groups")
        assert "AddressGroup" in links
