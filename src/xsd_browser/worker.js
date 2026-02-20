// Web Worker: runs Pyodide in a background thread so the UI stays responsive.

importScripts("https://cdn.jsdelivr.net/pyodide/v0.29.3/full/pyodide.js");

let pyodide;

function post(type, data) {
    self.postMessage({ type, data });
}

async function setup() {
    post('status', 'Loading Pyodide runtime...');
    pyodide = await loadPyodide();

    post('status', 'Installing lxml...');
    await pyodide.loadPackage(["lxml", "micropip"]);

    post('status', 'Installing Jinja2...');
    const micropip = pyodide.pyimport("micropip");
    await micropip.install("jinja2");

    post('status', 'Mounting project files...');
    const files = ['wasm.py', 'main.py', 'main.html.j2', 'main.css', 'main.js'];
    for (const f of files) {
        const resp = await fetch(f);
        const content = await resp.text();
        pyodide.FS.writeFile(`/home/pyodide/${f}`, content);
    }

    post('status', 'Importing Python modules...');
    await pyodide.runPythonAsync("import wasm");

    post('ready');
}

async function convert(files, entryPoint) {
    const xsdDir = "/home/pyodide/xsd_data";

    // Clean previous run
    post('status', 'Cleaning virtual filesystem...');
    await pyodide.runPythonAsync(`
import shutil, os
if os.path.exists("${xsdDir}"):
    shutil.rmtree("${xsdDir}")
os.makedirs("${xsdDir}")
`);

    // Write files to VFS (directories first, then files)
    const paths = Object.keys(files);
    const filePaths = paths.filter(p => files[p] !== null);

    for (const path of paths) {
        if (files[path] === null) {
            pyodide.FS.mkdirTree(`${xsdDir}/${path}`);
        }
    }
    for (let i = 0; i < filePaths.length; i++) {
        const path = filePaths[i];
        const parentDir = path.includes('/')
            ? `${xsdDir}/${path.substring(0, path.lastIndexOf('/'))}`
            : xsdDir;
        try { pyodide.FS.mkdirTree(parentDir); } catch(e) {}
        pyodide.FS.writeFile(`${xsdDir}/${path}`, files[path]);
        post('status', `Extracting (${i + 1}/${filePaths.length}): ${path}`);
    }

    post('status', `All ${filePaths.length} files extracted. Parsing XSD and rendering HTML...`);

    const entryPath = `${xsdDir}/${entryPoint}`;
    const result = pyodide.globals.get("wasm").process_data(entryPath);

    post('result', { html: result, entryPoint });
}

self.onmessage = async (e) => {
    const { type, files, entryPoint } = e.data;

    if (type === 'convert') {
        try {
            await convert(files, entryPoint);
        } catch (err) {
            post('error', err.message || String(err));
        }
    }
};

setup();
