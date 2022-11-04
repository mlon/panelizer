import argparse
import pathlib

from .convert import convert
from .generate import HP_TO_MM, generate_svg


def main() -> None:
    parser = argparse.ArgumentParser(
        "panelizer", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    parser_generate = subparsers.add_parser("generate")
    parser_generate.add_argument(
        "out", nargs="?", type=pathlib.Path, default="panel.svg"
    )
    parser_generate.add_argument(
        "--hp", required=True, type=int, choices=HP_TO_MM.keys()
    )
    parser_generate.add_argument("--name", type=str, required=True)

    parser_convert = subparsers.add_parser("convert")
    parser_convert.add_argument("file", type=pathlib.Path)
    parser_convert.add_argument(
        "--out", required=False, type=pathlib.Path, default=None
    )
    parser_convert.add_argument("--title", required=False, default=None)

    args = parser.parse_args()
    if args.command == "generate":
        generate_svg(hp=args.hp, name=args.name, filename=args.out)
    elif args.command == "convert":
        if args.out is None:
            args.out = args.file.name.replace(".svg", ".kicad_pcb")
        if args.title is None:
            args.title = args.file.name.replace(".svg", "")
        convert(input_filename=args.file, title=args.title, output_filename=args.out)


if __name__ == "__main__":
    main()
