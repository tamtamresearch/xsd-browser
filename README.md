# XSD by Example

`xsd_by_example.py` vezme XML Schema Definition (XSD) a vygeneruje přehledný HTML dokument, který ukazuje **příklad instance** odpovídající danému schématu.
Výstup kombinuje ukázkový XML dokument s anotacemi, takže je snadné pochopit strukturu, povinné prvky, typy a vazby.

Je to alternativa ke klasickým grafickým generátorům XSD dokumentace – cílem je být **čitelnější, kompaktnější a intuitivnější**.

---

## 📦 Funkce

- Načítá hlavní XSD a všechny `<xsd:import>` / `<xsd:include>`
- **Globální registr prefixů**: sbírá namespace→prefix mapování ze všech importovaných schémat, nejen z hlavního XSD. Tranzitivní importy (např. SFW → TEC → MMC) tak dostanou správné prefixy, i když je hlavní schéma nedeklaruje.
- Pokud žádné schéma nedeklaruje prefix pro daný namespace, odvodí ho z URI (např. `http://…/TEC_3_4` → `tec`)
- Typy z root namespace zůstávají bez prefixu; všechny ostatní importované typy jsou prefixovány
- Generuje HTML pomocí Jinja2 šablony
- Loguje průběh zpracování (na `stderr`)
- Výstup ukládá do souboru

---

## 🧭 Použití

python3 xsd_by_example.py input.xsd output.html

Příklad:

python3 xsd_by_example.py schema/SFW_1_1.xsd out.html

- `input.xsd` – hlavní XSD soubor
- `output.html` – cesta k výslednému HTML souboru

Logy se vypisují na `stderr`, aby nerušily HTML výstup.

---

## ⚡ Použití s uv

Projekt lze pohodlně spouštět pomocí **uv**, které se stará o virtuální prostředí i závislosti.

### Instalace uv

Linux/macOS:

curl -LsSf https://astral.sh/uv/install.sh  sh

Windows (PowerShell):

powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 (astral.sh in Bing)  iex"

### Instalace závislostí

V kořenovém adresáři projektu:

uv sync

### Spuštění nástroje

uv run xsd_by_example.py input.xsd output.html

Například:

uv run xsd_by_example.py schema/SFW_1_1.xsd out.html


Výhody:

- není potřeba ručně aktivovat `.venv`
- uv automaticky použije správné prostředí
- rychlé instalace a spouštění

---

## ⚠️ Omezení

Tento nástroj vznikl během víkendu a pokrývá jen část XSD specifikace.
Některé konstrukce nemusí být podporované a je dobré si výstup zkontrolovat.

---

## Changelog

### Persist details open/close state to localStorage

The open/close state of `<details>` elements (collapsible element refs and "Used by" boxes) is now persisted per hash in localStorage and restored on navigation.

**Features**:
- Each hash (e.g., `#element-Foo`, `#type-Bar`) independently remembers which elements are expanded
- State is saved on every toggle and before navigating away
- Back/forward browser navigation restores the previous expansion state
- Nested expansions are correctly restored (opening a parent loads children which may also need restoring)

**Implementation**:
- Storage key: `xbe-details-{document.title}` contains a JSON object keyed by hash
- Each entry stores `openElements` (array of element names) and `usagesOpen` (boolean)
- A capture-phase `toggle` listener saves state on every `<details>` toggle
- `showFromHash()` saves the old hash state before switching, then restores the new hash state after content is built
- Guard in `onCollapsibleElementRefToggle()` prevents duplicate content when async browser toggle fires after synchronous restore

### Globální registr namespace prefixů

Namespace prefixy se nově sbírají ze **všech** importovaných schémat, nejen z hlavního XSD. To řeší problém, kdy tranzitivní importy (např. SFW → TEC → MMC) ztrácely prefixy, protože hlavní schéma je nedeklarovalo.

- `ImportResolver` udržuje globální `ns_to_prefix` slovník, který se plní z `nsmap` každého načteného schématu
- Pokud žádné schéma nedeklaruje prefix pro daný namespace, odvodí se z URI (např. `http://…/TEC_3_4` → `tec`)
- Typy z root namespace zůstávají bez prefixu; všechny ostatní importy jsou prefixovány
- Cross-namespace reference (např. `mmc:MessageManagementContainer` uvnitř TEC) se přemapují přes globální registr; reference zpět na root namespace se stripují na neprefixovanou formu

**Příklad**: Při zpracování SFW_1_1.xsd se nyní TEC typy zobrazují jako `tec:TECMessage`, MMC typy jako `mmc:MessageManagementContainer`, LRC typy jako `lrc:LocationReferencingContainer` atd. Dříve byly tyto typy buď neprefixované, nebo nesprávně zpracované.

### Fix: `extended_by` macro not finding derived types

The "Extended by" section on complex type pages was always empty due to an XPath bug in `main.html.j2`.

**Root cause**: The XPath expression used `local-name(@base)` to try to extract the local part of the `@base` attribute's *value* (e.g., `"ApplicationRootMessageML"` from `"tsf:ApplicationRootMessageML"`). However, `local-name()` returns the local name of the *attribute node itself* — which is always the string `"base"`. The condition was therefore never true, and derived types were never displayed.

**Fix**: Replaced `local-name(@base)` with `substring-after(@base, ':')`, which correctly extracts the local part from prefixed attribute values. The existing `or @base="{name}"` fallback continues to handle the unprefixed case.

**Example**: For the abstract type `ApplicationRootMessageML`, types like `TECMessage` (which declare `<xs:extension base="tsf:ApplicationRootMessageML">`) are now correctly listed under "Extended by" when present in the merged schema.

### Fix: Cross-namespace type references not resolved (empty type contents)

Types referenced across namespace boundaries (e.g., `mmc:MessageManagementContainer` from within TEC_3_4.xsd) rendered as empty in the output because the JavaScript template lookup could not match the prefixed reference to the unprefixed type definition.

**Root cause**: The import resolver created an inconsistency between type *names* and type *references*:

1. Type `@name` attributes from imported schemas were never prefixed (only elements, groups, and attributeGroups were). So `MessageManagementContainer` stayed unprefixed in the merged document.
2. Type `@type` references that already had a cross-namespace prefix (e.g., `type="mmc:MessageManagementContainer"` in TEC_3_4.xsd) were left as-is because they contained a colon. But the `mmc:` prefix was only valid in TEC's context, not in the root document.
3. Extension/restriction `@base` attributes were not rewritten at all.

This caused the JavaScript `<xbe-ref>` lookup to search for `mmc:MessageManagementContainer` while the template was registered under `MessageManagementContainer` — no match, empty content.

**Fix** (three changes in `xsd_by_example.py` and one in `main.html.j2`):

1. **Prefix type names during import** (rule 1): `complexType` and `simpleType` `@name` attributes are now prefixed alongside elements/groups/attributeGroups, so that type names are consistent with references when the namespace IS in the root document's nsmap.
2. **Prefix `@base` attributes** (rule 4): Extension/restriction `@base` values are now prefixed using the same logic as `@type`.
3. **Resolve cross-namespace references** (rule 5, new): After rules 1–4, all prefixed `@type`, `@base`, `@ref`, and `@substitutionGroup` values are remapped through the imported schema's nsmap. The prefix is resolved to a namespace URI, then looked up in the root document's nsmap:
   - If the root has a prefix for that namespace → rewrite to use root's prefix
   - If the root uses it as default namespace or doesn't define it → strip the prefix (since types from that namespace were merged without prefix)
4. **Template `inherited_elements` macro**: No longer strips the namespace prefix from the base type name when looking up the parent type, since both names and references now use the same consistent prefix scheme.

**Example**: When processing SFW_1_1.xsd (which only defines `tdt:` in its nsmap), TEC_3_4.xsd's reference `type="mmc:MessageManagementContainer"` is now correctly stripped to `type="MessageManagementContainer"` (because MMC's namespace has no prefix in SFW). Meanwhile `type="tdt:DateTime"` correctly keeps its prefix (because `tdt:` IS defined in SFW's nsmap).

---

## 📝 Licence

AGPL-3.0-or-later
(c) 2023 David Koňařík
