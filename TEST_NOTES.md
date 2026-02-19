# Refactor tests: regex to lxml.html + XPath

## Summary

Replaced all regex-based HTML parsing in the test suite with `lxml.html.fromstring()` + XPath queries. Since `lxml` is already a project dependency, this adds zero extra cost while making tests structural and order-independent.

## Changes

### `tests/conftest.py` — rewrote all helpers

- `parse_html()` — new, parses HTML string into lxml document
- `get_template()` / `get_element_template()` — now take an lxml doc and return elements via XPath instead of regex-extracted strings
- `extract_element_names()` — now takes an lxml element, uses XPath `@element` attribute query
- `get_landing()` / `get_landing_section()` / `get_landing_links()` — all use XPath on the parsed doc
- `inner_html()` — new helper for backward-compat string assertions

### All 7 test files updated

Fixture renamed `rendered_html` to `doc`, returns parsed lxml doc instead of raw HTML string.

- `test_render_elements.py` — XPath for class checks, fixed `test_occurs_default_hidden` bug (`or` should have been `and`; replaced with proper XPath check on the specific element)
- `test_render_simple_types.py` — XPath for `<code>` elements, CSS class checks
- `test_render_attributes.py` — XPath for attribute elements, removed inline `re.split` logic
- `test_render_groups.py` — XPath for `xbe-ref` elements
- `test_render_landing.py` — XPath for landing div existence
- `test_render_usages.py` — simplified `_get_usage_links` to XPath `.//a` query
- `test_inherited_elements.py` — replaced all complex regex helpers with XPath-based `_get_inherited_from`, `_get_all_inherited_element_names`, `_get_own_element_names`

### Files not modified

- `test_import_resolver.py` — no HTML parsing, tests XSD import resolution directly
- `test_utils.py` — tests pure Python utility functions, no HTML parsing
- `src/xsd_browser/*` — no production code changes

## Verification

All 114 tests pass with identical semantics.
