#!/usr/bin/env python3
# This file is licenced under the GNU AGPLv3 or later
# (c) 2023 David Koňařík
import sys
from copy import deepcopy
from pathlib import Path
from collections import defaultdict

import lxml.etree
import lxml.objectify
import jinja2

def parse_xml(path):
    return lxml.etree.parse(path)

XSD = "http://www.w3.org/2001/XMLSchema"
def xpath(elem, query):
    return elem.xpath(query, namespaces={
        "xsd": XSD,
    })
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
    return lxml.etree.tostring(elem, pretty_print=True, ).decode()

def elem_type(elem):
    return {
        "element": "element",
        "simpleType": "type",
        "complexType": "type",
        "attributeGroup": "attribute-group"
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
        "data-substgroups": elem.attrib.get("substitutionGroup", ""),
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

    def handle_imports(self, doc, path):
        for include_el in xpath(doc, "xsd:include | xsd:import"):
            include_path = (path.parent / include_el.attrib["schemaLocation"]) \
                .resolve()
            if include_path in self.imported: continue
            self.imported.add(include_path)
            print("Importing", include_path, file=sys.stderr)

            include_doc = lxml.etree.parse(include_path)

            nsmap_additions = {}
            for prefix, namespace in include_doc.getroot().nsmap.items():
                if prefix is None: continue
                nsmap = self.main_doc.getroot().nsmap
                if prefix in nsmap and nsmap[prefix] != namespace:
                    print(f"Can't add namespace prefix {prefix} for {namespace}, "
                          f"since it is already used for {self.main_doc.getroot().nsmap[prefix]}",
                          file=sys.stderr)
                    continue
                nsmap_additions[prefix] = namespace
            if nsmap_additions != {}:
                new_nsmap = self.main_doc.getroot().nsmap | nsmap_additions
                lxml.etree.cleanup_namespaces(
                    self.main_doc,
                    top_nsmap=new_nsmap,
                    keep_ns_prefixes=[k for k in new_nsmap.keys() if k is not None])

            self.handle_imports(include_doc, include_path)

            add_prefix = ""
            if "namespace" in include_el.attrib:
                ns_to_prefix = {n: p for p, n in self.main_doc.getroot().nsmap.items()}
                add_prefix = ns_to_prefix[include_el.attrib["namespace"]] + ":"

            for el in xpath(include_doc, "//*[@name]"):
                if ":" not in el.attrib["name"]:
                    el.attrib["name"] = add_prefix + el.attrib["name"]
            for el in xpath(include_doc, "//*[@ref]"):
                if ":" not in el.attrib["ref"]:
                    el.attrib["ref"] = add_prefix + el.attrib["ref"]

            for el in xpath_one(include_doc, "//xsd:schema"):
                if el.tag == f"{{{XSD}}}annotation": continue
                self.main_schema_el.append(el)


if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <main.xsd>", file=sys.stderr)
    sys.exit(1)

main_doc_path = Path(sys.argv[1]).absolute()
main_doc = parse_xml(main_doc_path)

ImportResolver(main_doc).handle_imports(main_doc, main_doc_path)

# TODO: Automatically add xsd prefix and remap xsd name/ref fields
assert main_doc.getroot().nsmap.get("xsd") == XSD, \
    "Expected xsd prefix not found"

template_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(Path(__file__).parent),
    autoescape=True)
template_env.add_extension("jinja2.ext.do")
template_env.filters.update({
    "xpath": xpath,
    "xpath_one": xpath_one,
    "prettyprint_xml": prettyprint_xml,
    "elem_type": elem_type,
    "elem_path_attrs": elem_path_attrs,
    "elem_name_attrs": elem_name_attrs,
})

template = template_env.get_template("main.html.j2")
print(template.render(
    main_xml_path=main_doc_path,
    doc=main_doc,
    # Maps tuple of (type, name) to (type, name) tuples where the first
    # is referenced by the second
    usages_by_name=defaultdict(set),
))
