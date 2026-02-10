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

### Volitelné závislosti

Projekt má volitelnou závislost na `minify-html`, která umožňuje minifikaci výstupního HTML/JS/CSS. Instalace:

uv sync --extra minify

Poté lze při generování použít přepínač `--minify`:

uv run xsd-by-example input.xsd output.html --minify

Bez tohoto přepínače je výstup neminifikovaný (prázdné řádky jsou ale stále sloučeny).

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

See [CHANGELOG.md](CHANGELOG.md).

---

## 📝 Licence

AGPL-3.0-or-later
(c) 2023 David Koňařík
