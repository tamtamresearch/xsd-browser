/**
 * Builds a hierarchical path by traversing up the DOM tree.
 * Collects data-name attributes from ancestors until reaching an element
 * with data-belowroot (direct schema child). Skips TEMPLATE elements.
 * @param {HTMLElement} el - Starting element
 * @returns {string[]} Path segments from innermost to outermost (e.g., ["ChildElem", "ParentType"])
 */
function domElementPath(el) {
    const path = [];
    while(el.parentElement) {
        if(el.tagName.toUpperCase() != "TEMPLATE" && el.dataset.name) {
            path.push(el.dataset.name);
        }
        if(el.dataset.belowroot) {
            break;
        }
        el = el.parentElement;
    }
    return path;
}

/**
 * Finds the best matching template for a reference path.
 * Tries progressively shorter paths (full path, then dropping segments from end)
 * to find the most specific template. Falls back to name-only match if no
 * path-based match is found.
 * @param {string|null} type - Template type filter (e.g., "element-contents", "type-contents")
 * @param {string[]} path - Path segments to match against template data-path attributes
 * @returns {HTMLTemplateElement|null} Matching template element or null
 */
function closestTemplateForPath(type, path) {
    for(let i = path.length; i > 0; i--) {
        const cutPath = path.slice(0, i);
        const cutPathStr = cutPath.join("/");
        const templateEl = document.querySelector(
            (type ? `template[data-type="${type}"]` : "")
            + `[data-path="${cutPathStr}"]`);
        if(templateEl) return templateEl;
    }

    // Path based match failed, try any name
    return document.querySelector(
        (type ? `template[data-type="${type}"]` : "")
        + `[data-name="${path[0]}"]`);
}

/**
 * Removes empty attribute container boxes after template insertion.
 * Cleans up boxes (.complex-type-attrs, .extension-attrs, .restriction-attrs,
 * .attribute-group) that contain no .attribute children.
 * @param {HTMLElement} rootEl - Root element to search within
 */
function removeEmptyBoxes(rootEl) {
    rootEl.querySelectorAll(".complex-type-attrs, .extension-attrs,"
        + ".restriction-attrs, .attribute-group")
        .forEach(boxEl => {
            const isEmpty = boxEl.querySelectorAll(".attribute")
                                .length == 0;
            if(isEmpty) {
                boxEl.parentElement.removeChild(boxEl);
            }
        });
}

/**
 * Removes all child elements from a parent element.
 * @param {HTMLElement} el - Parent element to clear
 */
function removeChildren(el) {
    [...el.children].forEach(c => el.removeChild(c));
}

/**
 * Custom element that resolves XSD references by finding and cloning
 * matching template content. Core mechanism for lazy-loading schema documentation.
 * @customElement xbe-ref
 * @attr {string} ref - Name of the referenced element/type/group
 * @attr {string} [type] - Template type filter (e.g., "element-contents", "type-contents")
 */
class ReferenceElement extends HTMLElement {
    /** @inheritdoc */
    connectedCallback() {
        if(!this.isConnected) return; // MDN says I should have this

        const thisPath = domElementPath(this);
        const path = [this.getAttribute("ref"), ...thisPath];
        const type = this.getAttribute("type");
        const template = closestTemplateForPath(type, path);
        if(!template) {
            console.error(`No template for ${path}! (type ${type})`);
            return;
        }
        const contentEl = template.content.cloneNode(true);
        /*contentEl.prepend(
            document.createComment(
                `Loaded ${template.dataset.path} for path ${path}`));*/
        this.appendChild(contentEl);
        removeEmptyBoxes(this);
    }
}
customElements.define("xbe-ref", ReferenceElement);

/**
 * Custom element that creates an expandable/collapsible element view.
 * Displays the element header with a toggle to show/hide contents.
 * Also recursively displays elements from substitution groups.
 * @customElement xbe-collapsible-element-ref
 * @attr {string} element - Name of the XSD element to display
 */
class CollapsipleElementRefElement extends HTMLElement {
    /** @inheritdoc */
    connectedCallback() {
        if(!this.isConnected) return;

        this.afterHeadContent = this.querySelector("[slot=after-head]");
        const element = this.getAttribute("element");


        removeChildren(this);
        this.addElement(this, element);

        const addFromSubstGroup = (parent, substGroup) => {
            const substituents = document.querySelectorAll(
                `[data-type=element-head][data-substgroup="${substGroup}"]`);
            if(substituents.length > 0) {
                const box = document.createElement("div");
                box.classList.add("substitution-group");
                const origin = document.createElement("div");
                origin.classList.add("origin");
                origin.innerText = `Substitution group ${element}`;
                box.appendChild(origin);
                substituents.forEach(subst => {
                    this.addElement(box, subst.dataset.path);
                });
                substituents.forEach(subst => {
                    addFromSubstGroup(box, subst.dataset.name);
                });
                parent.appendChild(box);
            }
        }
        addFromSubstGroup(this, element);
    }

    /**
     * Creates a collapsible details element for an XSD element.
     * Clones the collapsible-element-ref-template, substitutes the element
     * name into placeholders, and appends to the container.
     * @param {HTMLElement} base - Container to append the element to
     * @param {string} element - Name of the XSD element
     */
    addElement(base, element) {
        const template = document.getElementById(
            "collapsible-element-ref-template");
        const baseContentEl = template.content.cloneNode(true);
        const detailsEl = baseContentEl.querySelector("details");
        detailsEl.dataset.element = element;
        baseContentEl
            .querySelectorAll(".simple, .element-end")
            .forEach(el =>
                el.innerText = el.innerText.replaceAll("ELEMENT", element));
        baseContentEl.querySelector("xbe-ref").setAttribute("ref", element);
        const afterHeadSlot =
            baseContentEl.querySelector("slot[name=after-head]");
        if(this.afterHeadContent)
            [...this.afterHeadContent.children].forEach(
                c => afterHeadSlot.appendChild(c));

        base.appendChild(baseContentEl);
    }
}
customElements.define("xbe-collapsible-element-ref",
    CollapsipleElementRefElement);

/**
 * Handles toggle events on collapsible element details.
 * Lazy-loads element contents when opened (creates xbe-ref),
 * removes content when closed to save memory.
 * @param {HTMLDetailsElement} detailEl - The details element being toggled
 */
function onCollapsibleElementRefToggle(detailEl) {
    const elemName = detailEl.dataset.element;
    const contentsEl = detailEl.querySelector(":scope > .element-contents");
    if(detailEl.open) {
        if(!contentsEl.querySelector(":scope > xbe-ref")) {
            const refEl = document.createElement("xbe-ref");
            refEl.setAttribute("type", "element-contents");
            refEl.setAttribute("ref", elemName);
            contentsEl.appendChild(refEl);
        }
    } else {
        const refEl = contentsEl.querySelector(":scope > xbe-ref");
        if(refEl) refEl.parentElement.removeChild(refEl);
    }
}

/**
 * Replaces the main content area with new content.
 * @param {DocumentFragment|HTMLElement} el - Content to display
 */
function setMainContent(el) {
    const mainEl = document.querySelector("main");
    removeChildren(mainEl);
    mainEl.appendChild(el);
}

/**
 * Displays an element's full documentation in the main area.
 * Shows element definition, type information, and collapsible instance view.
 * @param {string} element - Name of the XSD element to display
 */
function showElement(element) {
    if(!document.querySelector(
        `template[data-type="element-contents"][data-name="${element}"]`)) {
        alert(`No such element: ${element}`);
        return;
    }

    const template = document.getElementById("root-element-template");
    const contentEl = template.content.cloneNode(true);

    contentEl.querySelectorAll("h2").forEach(el => {
        el.innerText = el.innerText.replace("ROOT_ELEM", element);
    });
    contentEl.querySelector("xbe-ref").setAttribute("ref", element);
    contentEl.querySelector("xbe-collapsible-element-ref")
        .setAttribute("element", element);

    setMainContent(contentEl);
}

/**
 * Displays a type's full documentation in the main area.
 * Shows type definition, attributes, child elements, and inheritance info.
 * @param {string} type - Name of the XSD type to display
 */
function showType(type) {
    if(!document.querySelector(
        `template[data-type="type-contents"][data-name="${type}"]`)) {
        alert(`No such type: ${type}`);
        return;
    }

    const template = document.getElementById("root-type-template");
    const contentEl = template.content.cloneNode(true);

    contentEl.querySelectorAll("h2").forEach(el => {
        el.innerText = el.innerText.replace("ROOT_TYPE", type);
    });
    contentEl.querySelectorAll("xbe-ref").forEach(refEl => {
        refEl.setAttribute("ref", type);
    });

    setMainContent(contentEl);
}

/**
 * Displays a group's full documentation in the main area.
 * Shows group definition and contained elements.
 * @param {string} group - Name of the XSD group to display
 */
function showGroup(group) {
    if(!document.querySelector(
        `template[data-type="group-contents"][data-name="${group}"]`)) {
        alert(`No such group: ${group}`);
        return;
    }

    const template = document.getElementById("root-group-template");
    const contentEl = template.content.cloneNode(true);

    contentEl.querySelectorAll("h2").forEach(el => {
        el.innerText = el.innerText.replace("ROOT_GROUP", group);
    });
    contentEl.querySelectorAll("xbe-ref").forEach(el => {
        el.setAttribute("ref", group);
    });

    setMainContent(contentEl);
}

/**
 * Displays the landing page with categorized links to all definitions.
 * Shown when no hash is present or hash doesn't match any known prefix.
 */
function showLanding() {
    const template = document.getElementById("landing-template");
    const contentEl = template.content.cloneNode(true);
    setMainContent(contentEl);
}

/** @type {string} Current URL hash (without #) for state tracking */
let currentHash = '';

/** @type {boolean} Flag to prevent saving state while restoring */
let restoringState = false;

/**
 * Returns the localStorage key for storing details open/close state.
 * Key is unique per document (based on document.title).
 * @returns {string} Storage key in format "xbe-details-{title}"
 */
function getDetailsStorageKey() {
    return 'xbe-details-' + document.title;
}

/**
 * Retrieves all saved details state from localStorage.
 * @returns {Object.<string, {openElements: string[], usagesOpen: boolean}>}
 *          Map of hash -> state object
 */
function getAllDetailsState() {
    try {
        return JSON.parse(localStorage.getItem(getDetailsStorageKey())) || {};
    } catch(e) {
        return {};
    }
}

/**
 * Saves the current open/close state of all details elements for a hash.
 * Records which collapsible elements are expanded and whether the
 * "Used by" box is open.
 * @param {string} hash - URL hash to save state for
 */
function saveDetailsStateForHash(hash) {
    if (!hash) return;
    const state = getAllDetailsState();
    const openElements = [];
    document.querySelectorAll('main details.collapsible-element-ref[open]')
        .forEach(d => {
            if (d.dataset.element) openElements.push(d.dataset.element);
        });
    const usagesBox = document.querySelector('main details.usages-box');
    state[hash] = {
        openElements,
        usagesOpen: usagesBox ? usagesBox.open : false
    };
    try {
        localStorage.setItem(getDetailsStorageKey(), JSON.stringify(state));
    } catch(e) {}
}

/**
 * Saves details state for the current hash.
 * Convenience wrapper around saveDetailsStateForHash.
 */
function saveDetailsState() {
    saveDetailsStateForHash(currentHash);
}

/**
 * Restores saved open/close state of details elements for current hash.
 * Opens previously expanded elements in a loop (since opening a parent
 * may reveal children that also need restoring). Sets restoringState flag
 * to prevent save-on-toggle during restoration.
 */
function restoreDetailsState() {
    if (!currentHash) return;
    const state = getAllDetailsState();
    const hashState = state[currentHash];
    if (!hashState) return;
    restoringState = true;
    try {
        if (hashState.usagesOpen) {
            const usagesBox = document.querySelector('main details.usages-box');
            if (usagesBox) usagesBox.open = true;
        }
        if (hashState.openElements && hashState.openElements.length > 0) {
            const openSet = new Set(hashState.openElements);
            let changed = true;
            while (changed) {
                changed = false;
                document.querySelectorAll(
                    'main details.collapsible-element-ref:not([open])')
                    .forEach(d => {
                        if (openSet.has(d.dataset.element)) {
                            d.open = true;
                            onCollapsibleElementRefToggle(d);
                            changed = true;
                        }
                    });
            }
        }
    } finally {
        restoringState = false;
    }
}

/**
 * Main navigation handler - parses URL hash and displays appropriate content.
 * Saves state for previous hash before switching, then restores state for
 * new hash after content is built. Supports hash formats:
 * - #element-{name} -> showElement()
 * - #type-{name} -> showType()
 * - #group-{name} -> showGroup()
 */
function showFromHash() {
    if (currentHash) {
        saveDetailsStateForHash(currentHash);
    }
    const hash = window.location.hash.substring(1);
    currentHash = hash;
    if(hash.startsWith("element-")) {
        showElement(hash.substring(8));
    } else if(hash.startsWith("type-")) {
        showType(hash.substring(5));
    } else if(hash.startsWith("group-")) {
        showGroup(hash.substring(6));
    } else {
        showLanding();
    }
    restoreDetailsState();
}

// Initialize: handle hash on page load and hash changes
window.addEventListener("hashchange", showFromHash);
window.addEventListener("DOMContentLoaded", showFromHash);

// Save details state on every toggle (capture phase to catch before bubbling)
document.addEventListener('toggle', function(e) {
    if (restoringState) return;
    if (e.target.closest('main')) saveDetailsState();
}, true);
