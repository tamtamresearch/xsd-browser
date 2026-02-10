# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- **Landing page with categorized index of all definitions** — When no hash is present (or the hash doesn't match any known definition), a landing page is now displayed instead of a blank content area. It shows all schema definitions as clickable links grouped into sections: Elements, Complex Types, Simple Types, and Groups. Each section uses a responsive multi-column layout.
- **Persist details open/close state to localStorage** — The open/close state of `<details>` elements (collapsible element refs and "Used by" boxes) is now persisted per hash in localStorage and restored on navigation. Each hash independently remembers which elements are expanded. Back/forward browser navigation restores the previous expansion state.
- **Show root namespace prefix when explicitly declared in schema** — When a root XSD schema declares an explicit prefix for its own `targetNamespace` (e.g., `xmlns:d2="..."` matching `targetNamespace`), root elements now display with that prefix (e.g., `d2:payload` instead of `payload`).
- **Make remaining builtin type references clickable links** — Builtin XSD type names (e.g., `xsd:string`) in "Restriction of:", "List of:", union memberTypes, and element type fallback contexts are now rendered as clickable links to the W3C XML Schema spec.
- **Normalize XSD built-in type prefixes and link to W3C spec** — XSD built-in types are now normalized to the canonical `xsd:` prefix regardless of which prefix the source schemas use (`xs:`, `xsd:`, etc.). Built-in types link to the relevant section of the W3C XML Schema Part 2 specification.
- **Make inherited type names clickable links** — "Inherited attributes from X:" and "Inherited from X:" labels now render the base type name as a clickable link navigating to the type's definition.
- **Global namespace prefix registry** — Namespace prefixes are now collected from all imported schemas, not just the root XSD. This ensures transitive imports (e.g., SFW -> TEC -> MMC) get proper prefixes even when the root schema doesn't declare them. If no schema declares a prefix for a namespace, one is derived from the URI (e.g., `http://.../TEC_3_4` -> `tec`).
- **Optional HTML minification with `--minify` flag** — The `minify-html` dependency is now optional. Install with `uv sync --extra minify` and pass `--minify` to enable HTML/JS/CSS minification. CLI now uses `argparse`.

### Fixed

- **Hide empty "New attributes:" and "Allowed attributes:" headings** — Bare headings were shown even when `child_attributes()` produced no content. Fixed by capturing macro output and only rendering the heading when non-empty.
- **Crash on schemas with anonymous (inline) complex types** — `extended_by` macro now checks for `name` attribute before accessing it.
- **"Used by" links for local elements** — The "Used by" section showed broken links for local elements (elements defined inside complex types). Fixed by searching by `data-name` attribute instead of `data-path`.
- **`extended_by` macro not finding derived types** — The XPath expression used `local-name(@base)` which returns the attribute node name (`"base"`), not the attribute value's local part. Replaced with `substring-after(@base, ':')`.
- **Cross-namespace type references not resolved (empty type contents)** — Types referenced across namespace boundaries rendered as empty because the JavaScript template lookup could not match prefixed references to unprefixed type definitions. Fixed by prefixing type names during import and remapping cross-namespace references through the global registry.

### Changed

- **Refactor: Externalize CSS and JS from main.html.j2** — Split the monolithic template into separate `main.js` and `main.css` files for better maintainability. The generated HTML output is unchanged (still a single self-contained file).
