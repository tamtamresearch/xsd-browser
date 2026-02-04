# xsd-by-example

## Purpose

Renders XSD (XML Schema Definition) files into interactive single-page HTML documentation for reference/documentation purposes. The output is a self-contained HTML file with no external dependencies.

## Project Structure

```
xsd_by_example.py   - Main (and only) application file. Python CLI entry point.
main.html.j2        - Jinja2 template that generates the output HTML (contains HTML, CSS, JS, and Jinja2 macros).
pyproject.toml       - Project config. Entry point: xsd-by-example = "xsd_by_example:main"
output/              - Generated HTML output directory (not tracked in git).
```

## How to Run

```bash
xsd-by-example <input.xsd> <output.html>
```

Example:
```bash
xsd-by-example c:\Work\TTR\tpeg\tpeg\working\tec-01\schema\SFW_1_1.xsd output\x.html
```

## Dependencies

- **lxml** - XML/XSD parsing, XPath queries, pretty-printing
- **jinja2** - HTML template rendering (uses `jinja2.ext.do` extension)
- Build system: **hatchling**
- Linting: **ruff** (line-length 100, Python 3.10+)

## Architecture

### Python side (`xsd_by_example.py`)

1. **Parse** the root XSD file with `lxml.etree.parse()`
2. **Resolve imports** via `ImportResolver` class:
   - Recursively processes `<xs:include>` and `<xs:import>` elements
   - Merges all imported schema definitions into the main document's `<xs:schema>` element
   - Handles namespace prefix mapping: looks up the imported namespace in the root document's `nsmap` and prefixes `name`/`ref`/`type` attributes accordingly
   - Skips `<xs:annotation>` elements from imported schemas
   - Tracks already-imported paths to avoid duplicates
3. **Render** the merged document through the Jinja2 template (`main.html.j2`)
4. **Write** the output HTML file

Key utility functions exposed as Jinja2 filters:
- `xpath(elem, query)` / `xpath_one(elem, query)` - XPath with `xsd:` namespace
- `prettyprint_xml(elem)` - Pretty-print XML stripping namespaces
- `elem_type(elem)` - Maps XSD tag to category: `element`, `type`, `group`, `attribute-group`
- `elem_path_attrs(elem)` / `elem_name_attrs(elem)` - Generate HTML `data-*` attributes for DOM identification

### Template side (`main.html.j2`)

Generates a **self-contained HTML file** with embedded CSS and JavaScript. The rendering architecture uses HTML `<template>` elements and Web Components:

**Jinja2 macros (server-side, during render):**
- Iterates over all named XSD elements, complex types, simple types, groups, and attribute groups
- For each, generates `<template>` elements with `data-type` and `data-path` attributes
- Template types: `element-head`, `element-contents`, `type-attrs`, `type-contents`, `group-contents`, `attribute-group`, `*-usages`
- Tracks cross-references via `usages_by_name` (defaultdict of sets)

**JavaScript (client-side, in browser):**
- `<xbe-ref>` custom element - Resolves references by finding matching `<template>` elements via `data-type`/`data-path` and cloning their content
- `<xbe-collapsible-element-ref>` custom element - Creates expandable/collapsible element views with substitution group support
- Hash-based navigation: `#element-NAME`, `#type-NAME`, `#group-NAME`
- Element picker via `<datalist>` autocomplete in the header

**Key Jinja2 macros:**
- `complex_type_contents` / `complex_type_attrs` - Render complex type children and attributes (handles extension/restriction inheritance)
- `simple_type_contents` - Render simple type (union, list, restriction)
- `child_elements` - Recursively renders child elements, choices, sequences, groups
- `child_attributes` - Renders attributes and attribute group references
- `element_occurs` - Shows minOccurs/maxOccurs badges
- `record_usage` / `usages_content` - Track and display where each definition is used
- `inherited_elements` - Shows elements inherited via extension/restriction base types
- `extended_by` - Shows which types extend a given type
- `elem_link` / `type_link` / `group_link` - Generate clickable cross-reference links

## XSD Schemas Location

- Root schemas per application: `c:\Work\TTR\tpeg\tpeg\working\<app>\schema\`
- Shared/common schemas: `c:\Work\TTR\tpeg\tpeg\working\schema\`
- Example root: `SFW_1_1.xsd` imports `TDT_2_1.xsd` and `TEC_3_4.xsd` from `../../schema/`
- The schemas use `xs:` prefix (not `xsd:`), but the app handles this via namespace URI matching

## Important Notes

- The XSD namespace constant is `http://www.w3.org/2001/XMLSchema` (variable `XSD`)
- Import resolution rewrites `name`/`ref`/`type` attributes with namespace prefixes when the imported schema's namespace has a prefix in the root document
- Elements, groups, and attributeGroups get prefixed; types in `@type` get prefixed unless they contain `:` or start with `xsd:`
- Log messages are in Czech (original author's language)
- The `usages_by_name` dict is passed into the template and mutated during render via the `record_usage` macro and `jinja2.ext.do`
- Only one app file (`xsd_by_example.py`) -- all changes go there or in `main.html.j2`
