# xsd-browser

Generate interactive, single-page HTML documentation from XSD (XML Schema) files.

> This project is a fork of [xsd_by_example](https://codeberg.org/dvdkon/xsd_by_example)
> by David Koňařík. It has been substantially extended and renamed to **xsd-browser** by
> Roman Hořeňovský for [TamTam Research s.r.o.](https://www.tamtamresearch.com/)

## Features

- Parses the root XSD and recursively resolves all `<xsd:import>` / `<xsd:include>` references
- **Global namespace prefix registry** — collects namespace-to-prefix mappings from all imported schemas (not just the root), so transitive imports get correct prefixes automatically
- Derives prefixes from namespace URIs when none are declared (e.g., `http://.../TEC_3_4` becomes `tec`)
- Generates a **self-contained HTML file** with no external dependencies (CSS and JS are embedded inline)
- Interactive navigation with hash-based routing (`#element-Name`, `#type-Name`, `#group-Name`)
- Landing page with categorized index of all definitions
- Collapsible element views with lazy-loaded content
- Cross-reference links between elements, types, and groups
- "Used by" sections showing where each definition is referenced
- XSD built-in types link to the W3C XML Schema specification
- Persistent open/close state via localStorage

## Installation

[uv](https://docs.astral.sh/uv/) is a fast Python package manager and runner. It is the recommended way to install and run `xsd-browser`.

### Install from GitHub

```bash
uv tool install "git+https://github.com/tamtamresearch/xsd-browser.git"
```

To uninstall:

```bash
uv tool uninstall xsd-browser
```

### Local development

```bash
uv sync
```

## Usage

```bash
xsd-browser input.xsd [output.html]
```

### Run without installing

```bash
uv tool run "git+https://github.com/tamtamresearch/xsd-browser.git" input.xsd [output.html]
```

### Run from local checkout

```bash
uv run xsd-browser input.xsd [output.html]
```

If `output.html` is omitted (or set to `-`), the result is written to stdout.

Output is minified by default. Use `--no-minify` to disable minification.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

AGPL-3.0-or-later

Original work (c) 2023 David Koňařík

Modified work (c) 2026 Roman Hořeňovský, TamTam Research s.r.o.
