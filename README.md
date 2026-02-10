# XSD by Example

`xsd_by_example.py` vezme XML Schema Definition (XSD) a vygeneruje přehledný HTML dokument, který ukazuje **příklad instance** odpovídající danému schématu.  
Výstup kombinuje ukázkový XML dokument s anotacemi, takže je snadné pochopit strukturu, povinné prvky, typy a vazby.

Je to alternativa ke klasickým grafickým generátorům XSD dokumentace – cílem je být **čitelnější, kompaktnější a intuitivnější**.

---

## 📦 Funkce

- Načítá hlavní XSD a všechny `<xsd:import>` / `<xsd:include>`
- Zachovává namespace prefixy definované v hlavním XSD
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

Jasně, Petr — tady máš hotové README.md, připravené k okamžitému vložení.
Je čisté, přehledné a obsahuje i sekci pro uv.

# XSD by Example

`xsd_by_example.py` vezme XML Schema Definition (XSD) a vygeneruje přehledný HTML dokument, který ukazuje **příklad instance** odpovídající danému schématu.  
Výstup kombinuje ukázkový XML dokument s anotacemi, takže je snadné pochopit strukturu, povinné prvky, typy a vazby.

Je to alternativa ke klasickým grafickým generátorům XSD dokumentace – cílem je být **čitelnější, kompaktnější a intuitivnější**.

---

## 📦 Funkce

- Načítá hlavní XSD a všechny `<xsd:import>` / `<xsd:include>`
- Zachovává namespace prefixy definované v hlavním XSD
- Generuje HTML pomocí Jinja2 šablony
- Loguje průběh zpracování (na `stderr`)
- Výstup ukládá do souboru

---

## 🧭 Použití


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

Namespace logika je zjednodušená – nástroj **nepřidává nové prefixy**, pouze používá ty, které jsou definované v hlavním XSD.  
Pokud importované schéma používá namespace bez prefixu, nástroj jej nepřemapuje.

---

## 📝 Licence

AGPL-3.0-or-later  
(c) 2023 David Koňařík