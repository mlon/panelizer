"""
Generates a KiCad PCB from an SVG file
"""
import html
import math
from copy import deepcopy
from io import BytesIO
from typing import Optional

import cairosvg
import cairosvg.colors
import cssutils
import gingerbread._sexpr as s
import gingerbread.pcb
from gingerbread._geometry import bezier_to_points
from gingerbread.trace import trace
from lxml import etree
from lxml.etree import QName
from svgelements import SVG, Circle, CubicBezier, Line, Path, Rect

PADDING = 0.5

def gr_circle(
    *,
    center: tuple[float, float],
    end: tuple[float, float],
    layer: str | s.S = s.layer("F.Cu"),
    width: float = 0.127,
    fill: bool = False,
):
    # pylint: disable-next=protected-access
    layer = s._layer_or_str(layer)

    return s.S(
        "gr_circle",
        s.S("center", *center),
        s.S("end", *end),
        layer,
        s.width(width),
        s.fill(fill),
        s.tstamp(),
    )


s.gr_circle = gr_circle


class PCB(gingerbread.pcb.PCB):
    def add_circle(
        self, x, y, d, *, layer: str, fill: bool = False, width: float = 0.15
    ):
        self.items.append(
            s.gr_circle(
                center=(x, y),
                end=(x, y + d / 2),
                layer=layer,
                width=width,
                fill=fill,
            )
        )

    def add_plated_drill(self, x, y, d, pad_size):
        self.items.append(
            s.footprint(
                "PlatedDrillHole",
                s.pad(
                    "",
                    type="thru_hole",
                    shape="circle",
                    size=(d + 2 * pad_size, d + 2 * pad_size),
                    drill=s.drill(d),
                    layers="*.Cu *.Mask",
                    clearance=0.1,
                    zone_connect=0,
                ),
                at=(self.offset[0] + x, self.offset[1] + y),
            )
        )

    def add_plated_slotted_hole(
        self, x: float, y: float, pad_size: float, hole_size: float, slot_size: float
    ):
        self.items.append(
            s.footprint(
                "PlatedDrillSlottedHole",
                s.pad(
                    "",
                    type="thru_hole",
                    shape="roundrect",
                    size=(hole_size + 2 * pad_size, slot_size + 2 * pad_size),
                    drill=s.drill(oval=True, diameter=hole_size, width=slot_size),
                    layers="*.Cu *.Mask",
                    roundrect_rratio=0.5,
                    clearance=0.1,
                    zone_connect=0,
                ),
                at=(self.offset[0] + x, self.offset[1] + y),
            )
        )


def inkscape_label(node: etree._Element) -> str:
    nsmap = node.getroottree().getroot().nsmap
    return node.get(f"{{{nsmap['inkscape']}}}label")


def svg_tag(node: etree._Element, tag: str) -> str:
    nsmap = node.getroottree().getroot().nsmap
    return f"{{{nsmap['svg']}}}{tag}"


def inline_symbols(root: etree._Element) -> None:
    nsmap = root.nsmap
    nsmap.pop(None)

    symbol: etree._Element
    symbols: dict[str, etree._Element] = {}
    for symbol in root.xpath(".//svg:defs/svg:symbol", namespaces=nsmap):
        symbols[symbol.get("id")] = symbol
        symbol.getparent().remove(symbol)

    use: etree._Element
    for use in root.xpath("//svg:use", namespaces=nsmap):
        symbol = symbols.get(
            use.get(QName(nsmap["xlink"], "href").text).replace("#", "")
        )
        replacement = etree.Element("g", attrib={"transform": use.get("transform")})
        for child in symbol:
            replacement.append(deepcopy(child))
        use.getparent().replace(use, replacement)


def copy_node(node: etree._Element) -> etree._Element:
    if node == node.getroottree().getroot():
        return etree.Element(node.tag, attrib=node.attrib, nsmap=node.nsmap)
    else:
        new_node = etree.Element(node.tag, attrib=node.attrib)
        new_node.text = node.text
        return new_node


def recolor_node_children(
    node: etree._Element, force_fill: bool = False
) -> etree._Element:
    new_node = copy_node(node)

    style = cssutils.parseStyle(node.get("style", ""), validate=False)

    if new_node.get("fill") != "none" and new_node.get("fill") is not None:
        style["fill"] = new_node.get("fill")
        del new_node.attrib["fill"]

    fill = style["fill"]
    if force_fill or (fill != "" and fill is not None and fill != "none"):
        style["fill"] = "#000"

    if new_node.get("stroke") != "none" and new_node.get("stroke") is not None:
        style["stroke"] = new_node.get("stroke")
        del new_node.attrib["stroke"]

    stroke = style["stroke"]
    if stroke != "" and stroke is not None and stroke != "none":
        style["stroke"] = "#000"

    new_style = (
        html.unescape(style.getCssText(separator=""))
        .replace('"', "'")
        .replace(": ", ":")
    )

    if new_style != "":
        new_node.set("style", new_style)

    for child in node:
        new_node.append(recolor_node_children(child, force_fill))

    return new_node


def filter_node(
    node: etree._Element, layer: str, fill: bool = False
) -> Optional[etree._Element]:
    if inkscape_label(node) == layer and len(node) > 0:
        return recolor_node_children(node, fill)

    new_node = copy_node(node)
    for child in node:
        filtered_child = filter_node(child, layer, fill)
        if filtered_child is not None:
            new_node.append(filtered_child)

    return new_node if len(new_node) > 0 else None


def get_dimensions(svg: etree._ElementTree) -> tuple[float, float]:
    root = svg.getroot()
    width = float(root.get("width").replace("mm", ""))
    height = float(root.get("height").replace("mm", ""))
    return width, height


def add_cuts_layer(pcb: PCB, svg: etree._ElementTree) -> None:
    width, height = get_dimensions(svg)

    filtered_root = filter_node(svg.getroot(), "Cuts")
    if filtered_root is None:
        return

    pcb.add_rect(
        x=0,
        y=0,
        w=width,
        h=height,
        layer="Edge.Cuts",
        width=0.15,
        fill=False,
    )

    svg = SVG.parse(BytesIO(etree.tostring(etree.ElementTree(filtered_root))), ppi=25.4)

    shape: Circle | Path | Rect
    for shape in svg.select(lambda el: isinstance(el, (Circle, Path, Rect))):
        if isinstance(shape, Rect) and shape.ry is None:
            pcb.add_rect(
                x=shape.x,
                y=shape.y,
                w=shape.width,
                h=shape.height,
                layer="Edge.Cuts",
                width=0.15,
                fill=False,
            )
        elif isinstance(shape, Rect) and math.isclose(
            shape.ry, shape.height / 2, abs_tol=1e-6
        ):
            if shape.height <= 6.35:
                if shape.stroke.value is not None:
                    pcb.add_plated_slotted_hole(
                        shape.x + shape.width / 2,
                        shape.y + shape.height / 2,
                        shape.stroke_width,
                        shape.width - shape.stroke_width,
                        shape.height - shape.stroke_width,
                    )
                else:
                    pcb.add_slotted_hole(
                        shape.x + shape.width / 2,
                        shape.y + shape.height / 2,
                        shape.width,
                        shape.height,
                    )

        elif isinstance(shape, Circle):
            diameter = 2 * shape.rx - (shape.stroke_width or 0)
            if diameter > 6.35:
                if shape.stroke.value is not None:
                    for l in ["F.Cu", "B.Cu", "F.Mask", "B.Mask"]:
                        pcb.add_circle(
                            x=shape.cx,
                            y=shape.cy,
                            d=diameter + shape.stroke_width,
                            layer=l,
                            width=shape.stroke_width,
                        )
                pcb.add_circle(x=shape.cx, y=shape.cy, d=diameter, layer="Edge.Cuts")
            else:
                if shape.stroke.value is not None:
                    pcb.add_plated_drill(
                        x=shape.cx, y=shape.cy, d=diameter, pad_size=shape.stroke_width
                    )
                else:
                    pcb.add_drill(x=shape.cx, y=shape.cy, d=diameter)
        elif isinstance(shape, Path):
            shape.approximate_arcs_with_cubics()
            points = []
            for segment in shape.segments():
                if isinstance(segment, Line):
                    points.append((segment.start.x, segment.start.y))
                    points.append((segment.end.x, segment.end.y))
                elif isinstance(segment, CubicBezier):
                    points += bezier_to_points(
                        (segment.start.x, segment.start.y),
                        (segment.control1.x, segment.control1.y),
                        (segment.control2.x, segment.control2.y),
                        (segment.end.x, segment.end.y),
                        0.0001,
                    )
            pcb.add_poly(points, layer="Edge.Cuts")


def raster_svg(
    pcb: PCB,
    svg: etree._ElementTree,
    layer: str,
    *,
    invert: bool = False,
    dpi: int = 2540,
) -> None:
    tree = cairosvg.parser.Tree(bytestring=etree.tostring(svg))

    surface = cairosvg.surface.PNGSurface(
        tree,
        output=None,
        background_color="#fff",
        dpi=dpi,
        map_rgba=cairosvg.colors.negate_color if invert else lambda x: x,
    )
    surface.cairo.flush()
    # surface.cairo.write_to_png(f'{layer}.png')

    pcb.add_literal(
        trace(
            surface.cairo,
            layer=layer,
            dpi=dpi,
            center=False,
        )
    )


def add_copper_layers(pcb: PCB, svg: etree._ElementTree) -> None:
    width, height = get_dimensions(svg)

    holes_root = filter_node(svg.getroot(), "Cuts", fill=True)
    relief_root = filter_node(svg.getroot(), "Relief")

    nsmap = svg.getroot().nsmap
    nsmap.pop(None)

    for node in holes_root.xpath('.//svg:circle', namespaces=nsmap):
        node.set('r', str(float(node.get('r')) + PADDING))

    for node in holes_root.xpath('.//svg:rect', namespaces=nsmap):
        node.set('x', str(float(node.get('x')) - PADDING))
        node.set('y', str(float(node.get('y')) - PADDING))
        node.set('width', str(float(node.get('width')) + 2 * PADDING))
        node.set('height', str(float(node.get('height')) + 2 * PADDING))

    background = etree.Element(
        "rect",
        attrib={
            "fill": "#fff",
            "x": str(PADDING),
            "y": str(PADDING),
            "width": str(width - 2 * PADDING),
            "height": str(height - 2 * PADDING),
        },
    )
    holes_root.insert(0, background)
    raster_svg(pcb, etree.ElementTree(holes_root), "B.Cu", invert=True)

    for child in relief_root:
        holes_root.append(child)

    raster_svg(pcb, etree.ElementTree(holes_root), "F.Cu", invert=True)


def add_front_layer(pcb: PCB, svg: etree._ElementTree) -> None:
    front_root = filter_node(svg.getroot(), "Front")
    raster_svg(pcb, etree.ElementTree(front_root), "F.SilkS")


def add_alignment_footprints(pcb: PCB, svg: etree._ElementTree) -> None:
    max_height = 110
    width, height = get_dimensions(svg)
    filtered_root = filter_node(svg.getroot(), "Alignment")
    if filtered_root is None:
        return

    pcb.add_rect(
        0,
        (height - max_height) / 2,
        width,
        max_height,
        fill=False,
        layer="Dwgs.User",
    )

    svg = SVG.parse(BytesIO(etree.tostring(etree.ElementTree(filtered_root))), ppi=25.4)
    shape: Circle
    for shape in svg.select(lambda el: isinstance(el, Circle)):
        pcb.add_circle(
            shape.cx,
            shape.cy,
            2 * shape.rx,
            layer="Dwgs.User",
        )


def convert(input_filename: str, title: str, output_filename: str) -> None:
    svg = etree.parse(input_filename)
    inline_symbols(svg.getroot())

    panel = PCB(title=title, company="mlon")

    add_cuts_layer(panel, svg)
    add_front_layer(panel, svg)
    add_copper_layers(panel, svg)
    panel.write(output_filename)

    alignment = PCB(title=f"{title} - Alignement", company="mlon")
    add_alignment_footprints(alignment, svg)
    alignment.write(f"alignment-{output_filename}")
