# XSD by example

`xsd_by_example.py` takes a XML Schema Definition file and prints out an HTML
document describing the schema by providing an annotated "example". It shows
what a document following that schema looks like, while giving the user the
information necessary to imagine what other documents must look like.

It is an alternative to graphical schema generators that seem so prevalent in
XML-land, but never seemed intuitive or space-efficient to me.

## Usage:

```
python3 xsd_by_example.py input.xsd > output.html
```

## Disclaimer

This software was made over a weekend by someone who has read maybe 0.1% of the
XSD spec. It only handles part of the spec and relies on its user to notice
when it hits an unsupported part. It might work perfectly, or it might crash
and burn. It doesn't really understand XML namespaces and wishes they were just
simple prefixes.

Then again, it produces helpful outputs for
[NeTEx](https://github.com/NeTEx-CEN/NeTEx), and I really hope your schema
isn't even more complex.
