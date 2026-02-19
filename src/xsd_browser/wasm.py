import io
import zipfile
from lxml import etree
from jinja2 import Environment, FileSystemLoader
# from html_minifier.minify import minify_html
from main import render_html

def process_data(zip_uint8_proxy):
    # 1. Convert JS Uint8Array to Python Bytes
    # .to_py() is essential in Pyodide 0.29.3 to bridge the memory
    zip_bytes = zip_uint8_proxy.to_py().tobytes()
    
    parsed_items = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        for name in z.namelist():
            if name.lower().endswith('.xsd'):
                # Extract and parse XSD
                content = z.read(name)
                tree = etree.fromstring(content)
                # Sample logic: find element names
                names = tree.xpath("//*[local-name()='element']/@name")
                parsed_items.append({"filename": name, "elements": list(names)})

    # 2. Setup Jinja2 with the Virtual Filesystem Loader
    # index.html will write your .jinja files to /home/pyodide/
    file_loader = FileSystemLoader('/home/pyodide')
    env = Environment(loader=file_loader)
    
    # Add a custom filter if you need one
    env.filters['count'] = lambda x: len(x)

    # template = env.get_template('main.htmj.jinja')

    rendered = render_html("somewhere")

    # 3. Render
    # rendered = template.render(
    #     data=parsed_items,
    #     css_name="main.css",
    #     js_name="main.js"
    # )
    
    # Use html-minifier instead
    # TODO
    # return minify_html(rendered)
    return rendered
