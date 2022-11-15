import os
import os.path
from typing import NamedTuple

import typer
from lxml import etree
from lxml.etree import Element, ElementTree, QName, SubElement, _Element

HP_TO_MM = {
    2: 9.8,
    3: 15,
    4: 20,
    6: 30,
    8: 40.3,
    10: 50.5,
    12: 60.6,
    14: 70.8,
    16: 80.9,
    18: 91.30,
    20: 101.3,
    21: 106.3,
    22: 111.4,
    28: 141.9,
    42: 213,
}


class NS(NamedTuple):
    inkscape = "http://www.inkscape.org/namespaces/inkscape"
    sodipodi = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
    xlink = "http://www.w3.org/1999/xlink"
    svg = "http://www.w3.org/2000/svg"


def inkscape(tag: str) -> QName:
    return QName(NS.inkscape, tag)


def xlink(tag: str) -> QName:
    return QName(NS.xlink, tag)


def sodipodi(tag: str) -> QName:
    return QName(NS.sodipodi, tag)


LOCKED = {sodipodi("insensitive"): "true"}


def add_inkscape_helpers(parent: _Element, width: float, height: float) -> None:
    namedview = SubElement(
        parent,
        sodipodi("namedview"),
        attrib={
            inkscape("document-units"): "mm",
            "showgrid": "true",
            inkscape("current-layer"): "components",
            inkscape("zoom"): "1.8057555",
            inkscape("window-width"): "1792",
            inkscape("window-height"): "1067",
            inkscape("window-x"): "0",
            inkscape("window-y"): "25",
        },
    )

    SubElement(
        namedview,
        sodipodi("guide"),
        attrib={
            "position": "0,9.64",
            "orientation": "0,1",
            inkscape("color"): "#aaaaaa",
            inkscape("locked"): "true",
        },
    )

    SubElement(
        namedview,
        sodipodi("guide"),
        attrib={
            "position": "0,118.86",
            "orientation": "0,1",
            inkscape("color"): "#aaaaaa",
            inkscape("locked"): "true",
        },
    )

    SubElement(
        namedview,
        inkscape("grid"),
        attrib={
            "type": "xygrid",
            "units": "mm",
            "spacingx": "1.27",
            "spacingy": "1.27",
            "originx": str(width / 2),
            "originy": str(height / 2),
            "position": "0,118.25",
            "empspacing": "4",
            "color": "#aaaaaa",
            "opacity": "0.1",
            "empcolor": "#aaaaaa",
            "empopacity": "0.2",
        },
    )


def add_layer(parent: _Element, label: str, locked: bool = False) -> _Element:
    return SubElement(
        parent,
        "g",
        attrib={
            "id": label.lower(),
            inkscape("groupmode"): "layer",
            inkscape("label"): label,
            **(LOCKED if locked else {}),
        },
    )


def add_background(parent: _Element, width: float, height: float) -> None:
    SubElement(
        add_layer(parent, "Background", locked=True),
        "rect",
        attrib={
            "x": str(0),
            "y": str(0),
            "width": str(width),
            "height": str(height),
            "fill": "#000",
            inkscape("label"): "Background",
        },
    )


def add_mounting_hole(cuts: _Element, name: str, cx: float, cy: float) -> None:
    SubElement(
        cuts,
        "use",
        attrib={
            xlink("href"): "#mounting_hole",
            inkscape("label"): name,
            "transform": f"translate({cx - 4.1},{cy-2.6})",
            **LOCKED,
        },
    )


def add_mounting_holes(
    parent: _Element, panel_width: float, panel_height: float
) -> None:
    width = 6.4

    if panel_width < 2 * width:
        add_mounting_hole(
            parent,
            "Top",
            cx=panel_width / 2,
            cy=3,
        )
        add_mounting_hole(
            parent,
            "Bottom",
            cx=panel_width / 2,
            cy=panel_height - 3,
        )
    else:
        add_mounting_hole(parent, "Top Left", cx=7.5, cy=3)
        add_mounting_hole(
            parent,
            "Bottom Right",
            cx=panel_width - 7.5,
            cy=panel_height - 3,
        )
    if panel_width >= 7 * width:
        add_mounting_hole(parent, "Top Right", cx=panel_width - 7.5, cy=3)
        add_mounting_hole(
            parent,
            "Bottom Left",
            cx=7.5,
            cy=panel_height - 3,
        )


def add_logo(parent: _Element, x: float, y: float, width: float, height: float) -> None:
    # logo path is 100mm x 100mm
    SubElement(
        parent,
        "path",
        attrib={
            # pylint: disable-next=line-too-long
            "d": "M 17.227358,2.777814e-7 21.365959,4.1386824 C 11.783765,13.677804 5.8529026,26.881694 5.8529026,41.470817 c 0,29.092299 23.5838964,52.676265 52.6761114,52.676265 14.589228,0 27.793201,-5.930999 37.332316,-15.513391 L 100,82.772305 C 89.401708,93.41388 74.734492,100 58.529014,100 26.204333,100 1.4238009e-6,73.795593 1.4238009e-6,41.470817 1.4238009e-6,25.265438 6.5859818,10.598303 17.227358,2.777814e-7 Z M 25.651629,8.4243297 44.421211,27.193978 c -3.756853,3.713554 -6.084705,8.869671 -6.084705,14.569484 0,11.313675 9.171517,20.485215 20.485153,20.485215 5.6998,0 10.855902,-2.327861 14.569448,-6.084722 L 91.868183,74.640812 C 83.377299,83.250263 71.576364,88.58681 58.529014,88.58681 c -25.859745,0 -46.82321,-20.963527 -46.82321,-46.823348 0,-13.047319 5.336477,-24.848236 13.945825,-33.3391323 z",
            "fill": "#fff",
            inkscape("label"): "Logo",
            "transform": f"""
            translate({x - width / 2}, {y - height / 2}) 
            scale({width/100}, {height/100})
            """,
            **LOCKED,
        },
    )


def add_name(parent: _Element, cx: float, cy: float, name: str) -> None:
    SubElement(
        parent,
        "text",
        attrib={
            "x": str(cx),
            "y": str(cy),
            "dominant-baseline": "middle",
            "alignment-baseline": "central",
            "text-anchor": "middle",
            "fill": "#fff",
            "style": "font-weight:500;font-size:1.1mm;font-family:'Jost*';",
            inkscape("label"): "Module Name",
        },
    ).text = name


def add_relief(parent: _Element, width: float, height: float) -> None:
    thickness = 0.5
    SubElement(
        parent,
        "path",
        attrib={
            "d": f"M 0 {6 + thickness/2} L {width} {6 + thickness/2}",
            "stroke-width": str(thickness),
            "stroke": "#222",
            inkscape("label"): "Top Line",
            **LOCKED,
        },
    )
    SubElement(
        parent,
        "path",
        attrib={
            "d": f"M 0 {height - 6 - thickness/2} L {width} {height - 6 - thickness/2}",
            "stroke-width": str(thickness),
            "stroke": "#222",
            inkscape("label"): "Bottom Line",
            **LOCKED,
        },
    )


def add_symbols(parent: _Element) -> None:
    symbol_dir = os.environ.get(
        "PANELIZER_SYMBOLS",
        os.path.join(os.path.dirname(__file__), "..", "symbols"),
    )

    for symbol_file in os.listdir(symbol_dir):
        if not symbol_file.endswith(".svg"):
            continue
        symbol_name = os.path.splitext(symbol_file)[0].replace(" ", "_").lower()
        symbol_svg = etree.parse(os.path.join(symbol_dir, symbol_file))

        symbol = SubElement(parent, "symbol", attrib={"id": symbol_name})
        SubElement(symbol, "title").text = os.path.splitext(symbol_file)[0]
        for element in symbol_svg.getroot():
            if (
                element.tag == QName(NS.svg, "g")
                and element.get(inkscape("groupmode")) == "layer"
            ):
                symbol.append(element)


def main(
    filename: str, hp: float = typer.Option(...), name: str = "Untitled Module"
) -> None:
    height = 128.5
    width = HP_TO_MM[hp]

    root = Element(
        "svg",
        attrib={
            "height": f"{height}mm",
            "width": f"{width}mm",
            "viewBox": f"0 0 {width} {height}",
        },
        nsmap={
            "inkscape": NS.inkscape,
            "sodipodi": NS.sodipodi,
            "xlink": NS.xlink,
            None: NS.svg,
        },
    )
    add_inkscape_helpers(root, width, height)

    defs = SubElement(root, "defs")

    add_symbols(defs)

    add_background(root, width, height)

    add_layer(root, "Cuts")

    relief = add_layer(root, "Relief")
    if hp < 4:
        add_relief(relief, width, height - 5)
    else:
        add_relief(relief, width, height)

    front = add_layer(root, "Front")
    if hp <= 3:
        add_logo(front, width / 2, height - 8, 4, 4)
    elif hp == 4:
        add_logo(front, 4.4, height - 3, 4, 4)
    elif hp == 6:
        add_logo(front, 9.9, height - 3, 4, 4)
        add_name(front, 20.6, 3.2078741, name)
    elif hp == 8:
        add_logo(front, width / 2, height - 3, 4, 4)
        add_name(front, 25.75, 3.2078741, name)
    elif hp >= 10:
        add_name(front, width / 2, 3.2078741, name)
        add_logo(front, width / 2, height - 3, 4, 4)

    components = add_layer(root, "Components")
    add_mounting_holes(components, width, height)

    with open(filename, "wb") as f:
        f.write(etree.tostring(ElementTree(root), pretty_print=True))


if __name__ == "__main__":
    typer.run(main)
