"""Shared test helpers and fixtures for xsd-browser tests."""

import re
from pathlib import Path

SAMPLES_DIR = Path(__file__).resolve().parent / "samples"


def get_template(html: str, data_type: str, path: str) -> str:
    """Extract the content of a <template data-type="..." ... data-path="..."> block.

    Template tags span multiple lines and have other attributes between data-type
    and data-path (data-name, data-substgroup). We use [^>]* to stay within the
    opening tag (in Python regex, [^>] matches newlines too, unlike '.').
    """
    pattern = (
        rf'<template\s+data-type="{re.escape(data_type)}"'
        rf'[^>]*data-path="{re.escape(path)}"[^>]*>([\s\S]*?)</template>'
    )
    m = re.search(pattern, html)
    assert m, f"Template not found: data-type={data_type!r} data-path={path!r}"
    return m.group(1)


def get_element_template(html: str, data_type: str, name: str) -> str:
    """Extract element template by data-name attribute."""
    pattern = (
        rf'<template\s+data-type="{re.escape(data_type)}"'
        rf'[^>]*data-name="{re.escape(name)}"[^>]*>([\s\S]*?)</template>'
    )
    m = re.search(pattern, html)
    assert m, f"Template not found: data-type={data_type!r} data-name={name!r}"
    return m.group(1)


def extract_element_names(
    html_section: str,
) -> list[str]:
    """Extract element names from xbe-collapsible-element-ref tags."""
    return re.findall(
        r'<xbe-collapsible-element-ref\s+element="([^"]+)"',
        html_section,
    )


def get_landing(html: str) -> str:
    """Extract <div class="landing"> content from the landing template."""
    m = re.search(
        r"<div class=landing>([\s\S]*?)</template>",
        html,
    )
    assert m, "Landing section not found"
    return m.group(1)


def get_landing_section(html: str, heading: str) -> str:
    """Extract a section from the landing page by its h3 heading text."""
    landing = get_landing(html)
    pattern = rf"<h3>{re.escape(heading)}</h3>\s*<ul>([\s\S]*?)</ul>"
    m = re.search(pattern, landing)
    if not m:
        return ""
    return m.group(1)


def get_landing_links(html: str, heading: str) -> list[str]:
    """Extract link texts from a landing section."""
    section = get_landing_section(html, heading)
    return re.findall(r"<a[^>]*>([^<]+)</a>", section)
