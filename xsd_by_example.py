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

def log(msg):
    print(f"[INFO] {msg}", file=sys.stderr)

def parse_xml(path):
    log(f"Načítám XML: {path}")
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

    def handle_imports(self, doc, path):
        for include_el in xpath(doc, "xsd:include | xsd:import"):
            include_path = (path.parent / include_el.attrib["schemaLocation"]).resolve()
            if include_path in self.imported:
                continue

            self.imported.add(include_path)
            log(f"Importuji {include_path}")

            include_doc = lxml.etree.parse(include_path)
            include_schema = xpath_one(include_doc, "//xsd:schema")

            # zjistíme namespace
            ns = include_el.attrib.get("namespace") or include_schema.attrib.get("targetNamespace")
            add_prefix = ""

            if ns:
                # mapujeme namespace → prefix podle hlavního dokumentu
                ns_to_prefix = {n: p for p, n in self.main_doc.getroot().nsmap.items()}

                if ns in ns_to_prefix:
                    prefix = ns_to_prefix[ns]

                    if prefix is None:
                        # default namespace → nepřepisujeme
                        log(f"Namespace {ns} je defaultní (bez prefixu) – nepřepisuji @name/@ref")
                        add_prefix = ""
                    else:
                        # máme prefix → použijeme ho
                        add_prefix = prefix + ":"
                        log(f"Používám prefix '{prefix}:' pro namespace {ns}")

                else:
                    # namespace není v hlavním XSD → ignorujeme
                    log(f"Namespace {ns} není v hlavním XSD – nepřepisuji @name/@ref")
                    add_prefix = ""
            else:
                add_prefix = ""

            # rekurzivně zpracujeme importy uvnitř importovaného souboru
            self.handle_imports(include_doc, include_path)

            # pokud máme prefix, přepíšeme name/ref bez prefixu
            if add_prefix:
                # 1) Prefixujeme jen elementy, groupy a attributeGroup – ne typy
                for el in xpath(include_schema,
                                "xsd:element[@name] | xsd:group[@name] | xsd:attributeGroup[@name]"):
                    if ":" not in el.attrib["name"]:
                        el.attrib["name"] = add_prefix + el.attrib["name"]

                # 2) Prefixujeme ref (tam prefix dává smysl vždy)
                for el in xpath(include_schema, "//*[@ref]"):
                    if ":" not in el.attrib["ref"]:
                        el.attrib["ref"] = add_prefix + el.attrib["ref"]

                # 3) Prefixujeme typy v @type, pokud nejsou builtin
                for el in xpath(include_schema, "//*[@type]"):
                    t = el.attrib["type"]
                    if ":" not in t and not t.startswith("xsd:"):
                        el.attrib["type"] = add_prefix + t
            
            # přidáme obsah importovaného schema do hlavního
            for el in include_schema:
                if el.tag == f"{{{XSD}}}annotation":
                    continue
                self.main_schema_el.append(el)

def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.xsd> <output.html>", file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1]).absolute()
    output_path = Path(sys.argv[2]).absolute()

    log(f"Startuji generování dokumentace")
    log(f"Vstupní XSD: {input_path}")
    log(f"Výstupní HTML: {output_path}")

    if not input_path.exists():
        print(f"Soubor {input_path} neexistuje", file=sys.stderr)
        sys.exit(1)

    main_doc = parse_xml(input_path)

    log("Zpracovávám importy…")
    ImportResolver(main_doc).handle_imports(main_doc, input_path)

    log("Inicializuji Jinja2 šablonu…")
    template_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(Path(__file__).parent),
        autoescape=True
    )
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

    log("Renderuji HTML…")
    output = template.render(
        main_xml_path=input_path,
        doc=main_doc,
        usages_by_name=defaultdict(set),
    )

    log("Ukládám výstup…")
    output_path.write_text(output, encoding="utf-8")

    log("Hotovo.")

if __name__ == "__main__":
    main()