# xsd-browser

## Purpose

Renders XSD (XML Schema Definition) files into interactive single-page HTML documentation for reference/documentation purposes. The output is a self-contained HTML file with no external dependencies.

## Project Structure

```
src/xsd_browser/         - Python package (src layout)
  main.py                - Main application file. Python CLI entry point.
  main.html.j2           - Jinja2 template that generates the output HTML (uses includes for JS/CSS, contains Jinja2 macros).
  main.js                - JavaScript code included by main.html.j2 (custom elements, navigation, state management).
  main.css               - CSS styles included by main.html.j2 (typography, layout, components).
  __main__.py            - Enables `python -m xsd_browser` execution.
  __init__.py            - Package init (empty).
pyproject.toml           - Project config. Entry point: xsd-browser = "xsd_browser.main:main". Build backend: uv_build.
output/                  - Generated HTML output directory (not tracked in git).
```

## How to Run

```bash
xsd-browser <input.xsd> <output.html>
```

Example:
```bash
xsd-browser samples/DATEXII_3_Profile/DATEXII_3_D2Payload.xsd output/x.html
```

## Dependencies

- **lxml** - XML/XSD parsing, XPath queries, pretty-printing
- **jinja2** - HTML template rendering (uses `jinja2.ext.do` extension)
- **minify-html** - HTML minification (enabled by default, disable with `--no-minify`)
- Build system: **uv_build**
- Linting: **ruff** (line-length 100, Python 3.10+)

## Architecture

### Python side (`src/xsd_browser/main.py`)

1. **Parse** the root XSD file with `lxml.etree.parse()`
2. **Resolve imports** via `ImportResolver` class:
   - Recursively processes `<xs:include>` and `<xs:import>` elements
   - Merges all imported schema definitions into the main document's `<xs:schema>` element
   - **Global prefix registry** (`ns_to_prefix` dict): collects namespace→prefix mappings from ALL schemas encountered during import, not just the root. Seeded from the root document's `nsmap`, then extended by `_collect_prefixes_from_schema()` as each imported schema is parsed. This ensures transitive imports (e.g., SFW → TEC → MMC) get proper prefixes even when the root schema doesn't declare them.
   - **Prefix derivation fallback** (`_derive_prefix_from_ns()`): when no schema declares a prefix for a namespace (e.g., TEC uses default namespace for itself), derives one from the namespace URI (`http://…/TEC_3_4` → `tec`). Avoids collisions by appending a counter.
   - Root namespace types remain unprefixed; all other imported types get their namespace prefix prepended to `name`/`ref`/`type`/`base` attributes
   - Cross-namespace references (e.g., `mmc:MessageManagementContainer` inside TEC) are remapped using the global registry; references back to the root namespace are stripped to unprefixed form
   - Skips `<xs:annotation>` elements from imported schemas
   - Tracks already-imported paths to avoid duplicates
3. **Render** the merged document through the Jinja2 template (`main.html.j2`)
4. **Write** the output HTML file

Key utility functions exposed as Jinja2 filters:
- `xpath(elem, query)` / `xpath_one(elem, query)` - XPath with `xsd:` namespace
- `prettyprint_xml(elem)` - Pretty-print XML stripping namespaces
- `elem_type(elem)` - Maps XSD tag to category: `element`, `type`, `group`, `attribute-group`
- `elem_path_attrs(elem)` / `elem_name_attrs(elem)` - Generate HTML `data-*` attributes for DOM identification

### Template side (`main.html.j2`, `main.js`, `main.css`)

Generates a **self-contained HTML file** with embedded CSS and JavaScript. The template uses `{% include %}` directives to pull in `main.js` and `main.css` at render time. The rendering architecture uses HTML `<template>` elements and Web Components:

**Jinja2 macros (server-side, during render) - in `main.html.j2`:**
- Iterates over all named XSD elements, complex types, simple types, groups, and attribute groups
- For each, generates `<template>` elements with `data-type` and `data-path` attributes
- Template types: `element-head`, `element-contents`, `type-attrs`, `type-contents`, `group-contents`, `attribute-group`, `*-usages`
- Tracks cross-references via `usages_by_name` (defaultdict of sets)

**JavaScript (client-side, in browser) - in `main.js`:**
- `<xbe-ref>` custom element - Resolves references by finding matching `<template>` elements via `data-type`/`data-path` and cloning their content
- `<xbe-collapsible-element-ref>` custom element - Creates expandable/collapsible element views with substitution group support
- Hash-based navigation: `#element-NAME`, `#type-NAME`, `#group-NAME`
- Element picker via `<datalist>` autocomplete in the header
- State persistence via localStorage (details open/close state)

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

- Demo schemas: `samples/DATEXII_3_Profile/`
- Example root: `DATEXII_3_D2Payload.xsd` or `DATEXII_3_MessageContainer.xsd` from that directory
- The schemas use `xs:` prefix (not `xsd:`), but the app handles this via namespace URI matching

## Release Process

1. Update version in `pyproject.toml` (`version = "X.Y.Z"`) — this is the single source of truth, read at runtime via `importlib.metadata.version("xsd-browser")`
2. Move `[Unreleased]` entries in `CHANGELOG.md` to a new `## [X.Y.Z] - YYYY-MM-DD` section (keep an empty `[Unreleased]` header above it)
3. Commit: `Release X.Y.Z`
4. Tag: `git tag vX.Y.Z`
5. Merge to `master` and push with tags: `git push origin master --tags`

## Important Notes

- The XSD namespace constant is `http://www.w3.org/2001/XMLSchema` (variable `XSD`)
- Import resolution rewrites `name`/`ref`/`type`/`base`/`substitutionGroup` attributes with namespace prefixes from the global registry. Only the root document's own types remain unprefixed.
- Elements, groups, and attributeGroups get prefixed; types in `@type` and `@base` get prefixed unless they already contain `:` or start with `xsd:`
- The prefix registry is first-come-first-served: if two schemas declare different prefixes for the same namespace, the first one encountered wins
- Log messages are in Czech (original author's language)
- The `usages_by_name` dict is passed into the template and mutated during render via the `record_usage` macro and `jinja2.ext.do`
- All source lives in `src/xsd_browser/` -- main code in `main.py`, templates in `main.html.j2`, `main.js`, `main.css`
- Can be run as `xsd-browser` (CLI entry point), or `python -m xsd_browser`

## WASM Version

An experimental browser-only version that runs the full Python pipeline in-browser via Pyodide. No server required after initial load.

### Files

```
src/xsd_browser/
  index.html   - UI: file picker, entry dropdown, convert button, status
  worker.js    - Web Worker: loads Pyodide, installs deps, runs Python
  wasm.py      - Thin shim: calls render_html() from main.py with minify=False
```

### How to Run

Serve `src/xsd_browser/` over HTTP (required — `file://` won't work due to CORS):
```bash
python -m http.server --directory src/xsd_browser
```
Then open `http://localhost:8000`.

### Architecture

**`worker.js`** runs Pyodide v0.29.3 in a Web Worker (keeps UI responsive):
1. Loads Pyodide runtime
2. Installs `lxml` and `micropip` via `pyodide.loadPackage`
3. Installs `jinja2` via `micropip`
4. Fetches and writes project source files to VFS (`/home/pyodide/`): `wasm.py`, `main.py`, `main.html.j2`, `main.css`, `main.js`
5. Imports `wasm` module, posts `ready`

**`wasm.py`** is a thin shim — `process_data(entry_path_str)` calls `render_html()` from `main.py` with `minify=False` (minify-html is not available in Pyodide).

**Worker message protocol** (JS → worker):
- `{ type: 'convert', files, entryPoint }` — `files` is `{ path: Uint8Array | null }` dict (null = directory marker)

Worker → JS messages: `status` (progress text), `ready`, `result` (`{ html, entryPoint }`), `error`.

**`convert()` in worker.js:**
1. Cleans `/home/pyodide/xsd_data` via `shutil.rmtree` + `os.makedirs`
2. Writes all files from the dict to VFS (creates parent dirs as needed)
3. Calls `pyodide.globals.get("wasm").process_data(entryPath)`

### Input File Handling (all done in JS, in `index.html`)

| Format | How extracted | JS dependency |
|--------|--------------|---------------|
| `.xsd` | Read as ArrayBuffer directly | none |
| `.zip` | JSZip (CDN: cdnjs.cloudflare.com) | JSZip 3.10.1 |
| `.tar`, `.tar.gz`, `.tgz` | Inline `extractTar()` function | none (uses built-in `DecompressionStream` for gzip) |

All formats produce the same `files` dict sent to the worker's `convert` message — the worker has no format-specific code.

**`extractTar(file)` logic:**
- For `.tar.gz`/`.tgz`: pipes through `DecompressionStream('gzip')` first
- Parses raw tar bytes: 512-byte blocks, reads name (bytes 0–99), size (bytes 124–135, octal), type flag (byte 156); typeFlag `'0'` or `'\0'` = file, anything else = directory

### Key Constraints

- `DecompressionStream` requires a modern browser (Chrome 80+, Firefox 113+)
- Worker setup takes 30–60 seconds on first load (Pyodide + lxml download)
- The file input is disabled until the worker posts `ready`

## Git Commits

- Do NOT add `Co-Authored-By` signatures to commit messages
