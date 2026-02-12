# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Changed

- **"Extended by" section not collapsible** — Changed from non-functional `div`+`summary` to `details`+`summary` and matched "Used by" styling.
- **Independent state persistence for "Extended by"** — "Extended by" now has its own CSS class and localStorage key, so its open/close state persists independently from "Used by".
- **Incomplete inheritance hierarchy for multi-level chains** — For types with multi-level inheritance (e.g. TypeC extends TypeB extends TypeA), only the direct parent's elements were shown. Now the full chain is walked recursively, with a separate labeled "Inherited from X:" section for each ancestor (oldest first). Indirect ancestors no longer leak into "Used by" sections.

### Fixed

- **Inherited elements missing for types using complexContent/extension** ([#6](https://github.com/TamTamResearch/xsd-browser/issues/6)) — Types extending a base that itself uses `<xs:complexContent><xs:extension>` (e.g. `HierarchyElementGeneral` extending `fac:Facility`) were missing the base type's own elements in the "Inherited from" section.

## [0.2.0] - 2026-02-11

### Added

- **Landing page footer** — Added a slim footer bar at the bottom of the landing page with "Built with xsd-browser vX.X.X" (linked to GitHub) and "TamTam Research s.r.o." (linked to homepage). Styled to match the header color scheme.
- **Collapsible "About" block on landing page** — Shows source filename, generation timestamp, list of imported XSD files, schema stats (element/type/group counts), and generator version.
- **Collapsible "Schema Definitions" section on landing page** — Elements, Complex Types, Simple Types, and Groups are now wrapped in a single collapsible section (open by default) for better scannability.
- **Unified card styling for landing page sections** — Namespaces, Schema Definitions, and Generation Info sections share a consistent card look with bordered container, white background, and separator lines.

## [0.1.0] - 2026-02-11

### Added

- **Landing page with categorized index of all definitions** — When no hash is present (or the hash doesn't match any known definition), a landing page is now displayed instead of a blank content area. It shows all schema definitions as clickable links grouped into sections: Elements, Complex Types, Simple Types, and Groups. Each section uses a responsive multi-column layout.
- **Persist details open/close state to localStorage** — The open/close state of `<details>` elements (collapsible element refs and "Used by" boxes) is now persisted per hash in localStorage and restored on navigation. Each hash independently remembers which elements are expanded. Back/forward browser navigation restores the previous expansion state.
- **Show root namespace prefix when explicitly declared in schema** — When a root XSD schema declares an explicit prefix for its own `targetNamespace` (e.g., `xmlns:d2="..."` matching `targetNamespace`), root elements now display with that prefix (e.g., `d2:payload` instead of `payload`).
- **Make remaining builtin type references clickable links** — Builtin XSD type names (e.g., `xsd:string`) in "Restriction of:", "List of:", union memberTypes, and element type fallback contexts are now rendered as clickable links to the W3C XML Schema spec.
- **Normalize XSD built-in type prefixes and link to W3C spec** — XSD built-in types are now normalized to the canonical `xsd:` prefix regardless of which prefix the source schemas use (`xs:`, `xsd:`, etc.). Built-in types link to the relevant section of the W3C XML Schema Part 2 specification.
- **Make inherited type names clickable links** — "Inherited attributes from X:" and "Inherited from X:" labels now render the base type name as a clickable link navigating to the type's definition.
- **Global namespace prefix registry** — Namespace prefixes are now collected from all imported schemas, not just the root XSD. This ensures transitive imports (e.g., SFW -> TEC -> MMC) get proper prefixes even when the root schema doesn't declare them. If no schema declares a prefix for a namespace, one is derived from the URI (e.g., `http://.../TEC_3_4` -> `tec`).
- **Optional HTML minification with `--minify` flag** — The `minify-html` dependency is now optional. Install with `uv sync --extra minify` and pass `--minify` to enable HTML/JS/CSS minification. CLI now uses `argparse`.
- **Handle missing imported XSD files gracefully** — Missing imports now log a warning and continue instead of crashing.
- **DATEX II v3 sample schemas** — Added a complete set of DATEX II v3 Profile XSD files in `samples/DATEXII_3_Profile/` for testing and demonstration.

### Changed

- **Make `minify-html` a default dependency** — `minify-html` is now a regular dependency (no longer optional). Use `--no-minify` to disable minification.
- **Migrate to Python `logging` module** — Replaced custom `log()` function with standard `logging`, using f-string formatting.
- **Restructure to `uv` packaged application with src layout** — Moved from flat layout to `src/xsd_browser/` package. Switched build backend from hatchling to `uv_build`. Added `__main__.py` for `python -m xsd_browser` support. Can now be installed via `uv tool install` directly from GitHub.
- **Refactor: Externalize CSS and JS from main.html.j2** — Split the monolithic template into separate `main.js` and `main.css` files for better maintainability. The generated HTML output is unchanged (still a single self-contained file).

### Fixed

- **Hide empty "New attributes:" and "Allowed attributes:" headings** — Bare headings were shown even when `child_attributes()` produced no content. Fixed by capturing macro output and only rendering the heading when non-empty.
- **Ensure trailing newline when writing HTML to stdout**
- **Show friendly error when output directory does not exist**
- **Crash on schemas with anonymous (inline) complex types** — `extended_by` macro now checks for `name` attribute before accessing it.
- **"Used by" links for local elements** — The "Used by" section showed broken links for local elements (elements defined inside complex types). Fixed by searching by `data-name` attribute instead of `data-path`.
- **`extended_by` macro not finding derived types** — The XPath expression used `local-name(@base)` which returns the attribute node name (`"base"`), not the attribute value's local part. Replaced with `substring-after(@base, ':')`.
- **Cross-namespace type references not resolved (empty type contents)** — Types referenced across namespace boundaries rendered as empty because the JavaScript template lookup could not match prefixed references to unprefixed type definitions. Fixed by prefixing type names during import and remapping cross-namespace references through the global registry.
