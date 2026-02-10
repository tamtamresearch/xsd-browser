#!/usr/bin/env python3
# This file is licenced under the GNU AGPLv3 or later
# (c) 2023 David Koňařík

import re
import sys
from collections import defaultdict
from copy import deepcopy
from pathlib import Path

import jinja2
import lxml.etree
import lxml.objectify


def log(msg):
    print(f"[INFO] {msg}", file=sys.stderr)


def parse_xml(path):
    log(f"Loading XML: {path}")
    return lxml.etree.parse(path)


XSD = "http://www.w3.org/2001/XMLSchema"


def xpath(elem, query):
    return elem.xpath(query, namespaces={"xsd": XSD})


def xpath_one(elem, query):
    results = xpath(elem, query)
    return None if len(results) == 0 else results[0]


def prettyprint_xml(elem):
    elem = deepcopy(elem)
    for e in elem.iter():
        if isinstance(e.tag, str):
            e.tag = lxml.etree.QName(e.tag).localname
    if not isinstance(elem, lxml.etree._Comment):
        lxml.etree.cleanup_namespaces(elem)
    return lxml.etree.tostring(elem, pretty_print=True).decode()


def elem_type(elem):
    return {
        "element": "element",
        "simpleType": "type",
        "complexType": "type",
        "group": "group",
        "attributeGroup": "attribute-group",
    }[elem.tag.split("}")[1]]


def elem_path(elem):
    path = []
    while elem is not None:
        if "name" in elem.attrib:
            path.append(elem.attrib["name"])
        elem = elem.getparent()
    return path


def elem_path_attrs(elem):
    path = elem_path(elem)
    return {
        "data-name": path[0],
        "data-substgroup": elem.attrib.get("substitutionGroup", ""),
        "data-path": "/".join(path),
    }


def elem_name_attrs(elem):
    attrs = {}
    if "name" in elem.attrib:
        attrs["data-name"] = elem.attrib["name"]
    parent = elem.getparent()
    if parent is not None and parent.tag == f"{{{XSD}}}schema":
        attrs["data-belowroot"] = True
    return attrs


class ImportResolver:
    def __init__(self, main_doc):
        self.main_doc = main_doc
        self.main_schema_el = xpath_one(main_doc, "//xsd:schema")
        self.imported = set()
        # Global namespace → prefix registry
        self.ns_to_prefix = {}
        self.root_target_ns = self.main_schema_el.attrib.get("targetNamespace")
        # Detect if root schema declares an explicit prefix for its own targetNamespace
        self.root_prefix = ""
        if self.root_target_ns:
            for pfx, ns_uri in main_doc.getroot().nsmap.items():
                if pfx is not None and ns_uri == self.root_target_ns:
                    self.root_prefix = pfx
                    break
        # Seed from root document's nsmap
        for pfx, ns_uri in main_doc.getroot().nsmap.items():
            if pfx is not None and ns_uri != XSD and ns_uri not in self.ns_to_prefix:
                if ns_uri == self.root_target_ns and not self.root_prefix:
                    continue
                self.ns_to_prefix[ns_uri] = pfx

    def _collect_prefixes_from_schema(self, schema_el):
        for pfx, ns_uri in schema_el.nsmap.items():
            if pfx is None or ns_uri == XSD or ns_uri == self.root_target_ns:
                continue
            if ns_uri not in self.ns_to_prefix:
                self.ns_to_prefix[ns_uri] = pfx
                log(f"Registering prefix '{pfx}' for namespace {ns_uri}")

    def _derive_prefix_from_ns(self, ns_uri):
        last_part = ns_uri.rstrip("/").rsplit("/", 1)[-1]
        base = last_part.split("_", 1)[0].lower()
        candidate = base
        counter = 2
        used_prefixes = set(self.ns_to_prefix.values())
        while candidate in used_prefixes:
            candidate = f"{base}{counter}"
            counter += 1
        return candidate

    def handle_imports(self, doc, path):
        for include_el in xpath(doc, "xsd:include | xsd:import"):
            include_path = (path.parent / include_el.attrib["schemaLocation"]).resolve()
            if include_path in self.imported:
                continue

            self.imported.add(include_path)
            log(f"Importing {include_path}")

            include_doc = lxml.etree.parse(include_path)
            include_schema = xpath_one(include_doc, "//xsd:schema")

            # Collect prefixes from imported schema into global registry
            self._collect_prefixes_from_schema(include_schema)

            # Determine namespace and prefix for this import
            ns = include_el.attrib.get("namespace") or include_schema.attrib.get(
                "targetNamespace"
            )
            add_prefix = ""

            if ns and ns != self.root_target_ns:
                prefix = self.ns_to_prefix.get(ns)
                if not prefix:
                    prefix = self._derive_prefix_from_ns(ns)
                    self.ns_to_prefix[ns] = prefix
                    log(f"Deriving prefix '{prefix}' for namespace {ns}")
                add_prefix = prefix + ":"
                log(f"Using prefix '{add_prefix}' for namespace {ns}")
            elif ns == self.root_target_ns and self.root_prefix:
                add_prefix = self.root_prefix + ":"
                log(f"Namespace {ns} is root with prefix '{self.root_prefix}'")
            elif ns == self.root_target_ns:
                log(f"Namespace {ns} is root — not prefixing")

            # Recursively process imports within the imported file
            self.handle_imports(include_doc, include_path)

            # If we have a prefix, rewrite unprefixed name/ref
            if add_prefix:
                # 1) Prefix definition names
                for el in xpath(
                    include_schema,
                    "xsd:element[@name] | xsd:group[@name]"
                    " | xsd:attributeGroup[@name]"
                    " | xsd:complexType[@name] | xsd:simpleType[@name]",
                ):
                    if ":" not in el.attrib["name"]:
                        el.attrib["name"] = add_prefix + el.attrib["name"]

                # 2) Prefix ref attributes
                for el in xpath(include_schema, "//*[@ref]"):
                    if ":" not in el.attrib["ref"]:
                        el.attrib["ref"] = add_prefix + el.attrib["ref"]

                # 3) Prefix @type unless builtin
                for el in xpath(include_schema, "//*[@type]"):
                    t = el.attrib["type"]
                    if ":" not in t and not t.startswith("xsd:"):
                        el.attrib["type"] = add_prefix + t

                # 4) Prefix @base in extension/restriction
                for el in xpath(include_schema, "//*[@base]"):
                    b = el.attrib["base"]
                    if ":" not in b and not b.startswith("xsd:"):
                        el.attrib["base"] = add_prefix + b

            # 5) Remap cross-namespace prefixes via the global registry
            import_nsmap = include_schema.nsmap
            for attr in ("type", "base", "ref", "substitutionGroup"):
                for el in xpath(include_schema, f"//*[@{attr}]"):
                    val = el.attrib[attr]
                    if ":" not in val:
                        continue
                    local_prefix, local = val.split(":", 1)
                    ref_ns = import_nsmap.get(local_prefix)
                    if ref_ns == XSD:
                        el.attrib[attr] = "xsd:" + local
                        continue
                    if not ref_ns:
                        continue
                    if ref_ns == self.root_target_ns:
                        if self.root_prefix:
                            el.attrib[attr] = self.root_prefix + ":" + local
                        else:
                            el.attrib[attr] = local  # root namespace → strip prefix
                    else:
                        registry_prefix = self.ns_to_prefix.get(ref_ns)
                        if registry_prefix:
                            el.attrib[attr] = registry_prefix + ":" + local
                        else:
                            log(
                                f"WARNING: No registry prefix for {ref_ns},"
                                f" keeping '{val}'"
                            )

            # Append imported schema contents to the main document
            for el in include_schema:
                if el.tag == f"{{{XSD}}}annotation":
                    continue
                self.main_schema_el.append(el)


def _normalize_xsd_prefixes(schema_el, xsd_prefixes):
    """Rewrite any XSD-namespace prefix (e.g. xs:) to the canonical xsd: form."""
    for attr in ("type", "base"):
        for el in schema_el.iter():
            val = el.attrib.get(attr)
            if not val or ":" not in val:
                continue
            pfx, local = val.split(":", 1)
            if pfx in xsd_prefixes and pfx != "xsd":
                el.attrib[attr] = "xsd:" + local


def _prefix_root_elements(elements, add_prefix):
    """Prefix the root document's own definitions with the root namespace prefix."""
    for el in elements:
        tag = lxml.etree.QName(el.tag).localname if isinstance(el.tag, str) else None
        if tag in ("element", "group", "attributeGroup", "complexType", "simpleType"):
            name = el.attrib.get("name", "")
            if name and ":" not in name:
                el.attrib["name"] = add_prefix + name

    # Prefix ref/type/base/substitutionGroup on all descendants of original elements
    for root_el in elements:
        for attr in ("ref", "substitutionGroup"):
            for el in root_el.iter():
                val = el.attrib.get(attr)
                if val and ":" not in val:
                    el.attrib[attr] = add_prefix + val
        for attr in ("type", "base"):
            for el in root_el.iter():
                val = el.attrib.get(attr)
                if val and ":" not in val and not val.startswith("xsd:"):
                    el.attrib[attr] = add_prefix + val


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate HTML documentation from XSD")
    parser.add_argument("input", help="Input XSD file")
    parser.add_argument("output", help="Output HTML file")
    parser.add_argument("--minify", action="store_true", help="Minify HTML output")
    args = parser.parse_args()

    input_path = Path(args.input).absolute()
    output_path = Path(args.output).absolute()

    log(f"Starting documentation generation")
    log(f"Input XSD: {input_path}")
    log(f"Output HTML: {output_path}")

    if not input_path.exists():
        print(f"File {input_path} does not exist", file=sys.stderr)
        sys.exit(1)

    main_doc = parse_xml(input_path)

    log("Processing imports...")
    resolver = ImportResolver(main_doc)
    # Snapshot original root children before imports add more
    original_root_children = list(resolver.main_schema_el)
    resolver.handle_imports(main_doc, input_path)

    # If root schema declares an explicit prefix, prefix its own definitions
    if resolver.root_prefix:
        _prefix_root_elements(original_root_children, resolver.root_prefix + ":")

    # Normalize all XSD-namespace prefixes (e.g. xs:string) to canonical xsd: form
    xsd_prefixes = {
        pfx for pfx, ns_uri in main_doc.getroot().nsmap.items()
        if pfx is not None and ns_uri == XSD
    }
    if xsd_prefixes - {"xsd"}:
        _normalize_xsd_prefixes(resolver.main_schema_el, xsd_prefixes)

    log("Initializing Jinja2 template...")
    template_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(Path(__file__).parent),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template_env.add_extension("jinja2.ext.do")
    template_env.filters.update(
        {
            "xpath": xpath,
            "xpath_one": xpath_one,
            "prettyprint_xml": prettyprint_xml,
            "elem_type": elem_type,
            "elem_path_attrs": elem_path_attrs,
            "elem_name_attrs": elem_name_attrs,
        }
    )

    template = template_env.get_template("main.html.j2")

    log("Rendering HTML...")
    output = template.render(
        main_xml_path=input_path,
        doc=main_doc,
        usages_by_name=defaultdict(set),
        ns_to_prefix=resolver.ns_to_prefix,
        root_target_ns=resolver.root_target_ns,
    )

    output = re.sub(r'\n\s*\n', '\n\n', output)

    if args.minify:
        try:
            import minify_html
        except ImportError:
            print(
                "minify-html not installed. Install with: pip install xsd-by-example[minify]",
                file=sys.stderr,
            )
            sys.exit(1)
        log("Minifying HTML...")
        output = minify_html.minify(output, minify_js=True, minify_css=True)

    log("Writing output...")
    output_path.write_text(output, encoding="utf-8")

    log("Done.")


if __name__ == "__main__":
    main()
