from io import BytesIO

from lxml import etree
from lxml.etree import SubElement, _ElementTree

from .create import NS, QName, add_symbols


def update_symbols(svg: _ElementTree) -> None:
    root = svg.getroot()
    nsmap = root.nsmap
    nsmap["svg"] = nsmap.pop(None)

    defs_list = root.xpath(".//svg:defs", namespaces=nsmap)
    if len(defs_list) != 0:
        defs = defs_list[0]
        for element in defs:
            if element.tag == QName(NS.svg, "symbol"):
                defs.remove(element)
    else:
        defs = SubElement(root, "defs")

    add_symbols(defs)


def update(stream: BytesIO) -> BytesIO:
    svg = etree.parse(stream)

    update_symbols(svg)

    return BytesIO(etree.tostring(svg, pretty_print=True))
