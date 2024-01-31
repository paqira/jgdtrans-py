from __future__ import annotations

import argparse
import codecs
import glob
import json
import os
import re
import sys
import textwrap
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from itertools import chain
from pathlib import Path
from typing import Any, Final, Literal, TypeAlias

import tomlkit
from typing_extensions import Self

import JGDtrans

FormatType: TypeAlias = Literal["TKY2JGD", "PatchJGD", "PatchJGD_H", "HyokoRev", "SemiDynaEXE", "geonetF3", "ITRF2014"]


def guess_parser(format: str):
    if format in PARSER.keys():
        return format

    s = format.lower()
    if s.endswith("geonetf3"):
        return "geonetF3"
    elif s.endswith("itrf2014"):
        return "ITRF2014"
    elif s.startswith("hyokorev"):
        return "HyokoRev"
    elif s.endswith("_h"):
        return "PatchJGD_H"
    elif s.startswith("semidyna"):
        return "SemiDynaEXE"
    elif s == "tky2jgd":
        return "TKY2JGD"
    return "PatchJGD"


PARSER: Final = {
    "TKY2JGD": JGDtrans.TKY2JGD,
    "PatchJGD": JGDtrans.PatchJGD,
    "PatchJGD_H": JGDtrans.PatchJGD_H,
    "PatchJGD_HV": JGDtrans.PatchJGD_HV,
    "HyokoRev": JGDtrans.HyokoRev,
    "SemiDynaEXE": JGDtrans.SemiDynaEXE,
    "geonetF3": JGDtrans.geonetF3,
    "ITRF2014": JGDtrans.ITRF2014,
}


@dataclass
class TomlField:
    key: str
    path: str
    format: str | None
    toml: str
    encoding: str = "utf-8"
    description: str | None = None

    @classmethod
    def from_dict(cls, obj: Mapping[str, Any], toml: str) -> Self:
        key = obj["key"]
        path = obj["path"]
        format = obj["format"]
        encoding = obj.get("encoding", "UTF-8")
        description = obj.get("description", None)
        return cls(key=key, path=path, format=format, toml=toml, encoding=encoding, description=description)

    @classmethod
    def from_file(
        cls,
        key: str,
        path: str,
        format: str | None,
        toml: str,
        encoding: str = "utf-8",
    ):
        if Path(path).suffix.lower().endswith(".par"):
            parser = guess_parser(format)

            text = Path(path).read_text(encoding=encoding)
            tf = parser(text)
            return cls(key=key, path=path, format=format, toml=toml, encoding=encoding, description=tf.description)
        elif Path(path).suffix.lower().endswith(".json"):
            text = Path(path).read_text(encoding=encoding)
            obj = json.loads(text)
            return cls(
                key=key,
                path=path,
                format=format,
                toml=toml,
                encoding=encoding,
                description=obj.get("description", None),
            )
        elif Path(path).suffix.lower().endswith(".csv"):
            pass
        raise ValueError

    def to_dict(self) -> dict[str, str | None]:
        obj = asdict(self)
        del obj["toml"]
        return obj

    def abs_path(self):
        p = Path(self.path) if Path(self.path).absolute() else Path(self.toml) / self.path
        return os.fspath(p.absolute())

    def read(self):
        return Path(self.abs_path()).read_text(encoding=self.encoding)

    def transformer(self):
        p = Path(self.path)
        if p.suffix.endswith(".par"):
            if self.format is None:
                raise ValueError
            parser = PARSER[self.format]
            return parser(self.read())
        elif p.suffix.endswith(".json"):
            obj = json.loads(self.read())
            return JGDtrans.Transformer.from_dict(obj)
        elif p.suffix.endswith(".csv"):
            pass
        raise ValueError

    def summary(self, verbose: int = 0):
        path = self.abs_path()

        text = "\x1b[1m{fields.tag}\x1b[0m"
        if verbose < 1:
            text += f" ({path})\n"
        elif verbose == 1:
            text += f"path: {path}\n"
            if self.description is not None:
                desc = self.description.splitlines()[0]
                text += f"description: {desc}\n"
        else:
            encoding = codecs.lookup(self.encoding).name

            text += f"path: {path}\n"
            text += f"encoding: {encoding}\n"
            if self.format:
                text += f"format: {self.format}\n"
            if self.description:
                desc = textwrap.indent(self.description, prefix="> ")
                text += f"description:\n{desc}\n"
        return text


class TomlFile:
    path: str
    _contents: dict

    def __init__(self, path: str):
        self.path = path

        text = Path(path).read_text(encoding="utf-8")
        contents = tomlkit.loads(text)
        if "file" not in contents:
            raise ValueError

        self._contents = contents

    def __getitem__(self, item: str):
        for key, value in self.items():
            if key == item:
                return value
        raise KeyError(item)

    def write(self):
        contents = tomlkit.dumps(self._contents)
        Path(self.path).write_text(contents, encoding="utf-8")

    def keys(self):
        return [field["key"] for field in self._contents["file"]]

    def values(self):
        return [field for field in self._contents["file"]]

    def items(self):
        return [(field["key"], field) for field in self._contents["file"]]

    def append(self, item: TomlField):
        self._contents["file"].append(item.to_dict())

    def remove(self, item: str, regex: bool = False):
        removed = []
        remain = []
        if regex:
            pattern = re.compile(item)
            for field in self._contents["file"]:
                if pattern.match(field["key"]):
                    removed.append(field)
                else:
                    remain.append(field)
        else:
            for field in self._contents["file"]:
                if field["key"] == item:
                    removed.append(field)
                else:
                    remain.append(field)

        self._contents["file"] = remain
        return removed

    def transform(self, fields: Iterable[dict], keys: Sequence[str], backward: bool = False) -> list[dict]:
        head, rest = keys[0], keys[1:]
        result = []

        tf = self[head]
        for field in fields:
            try:
                res = tf.transform(
                    latitude=field["latitude"],
                    longitude=field["longitude"],
                    altitude=field.get("altitude", 0),
                    backward=backward,
                )
            except JGDtrans.ParameterNotFoundError:
                result.append({"error": field.get("error", []) + [head]})
            else:
                result.append(
                    {
                        **field,
                        "latitude": res.latitude,
                        "longitude": res.longitude,
                        "altitude": res.altitude,
                    }
                )

        if not rest:
            return result
        return self.transform(fields=result, keys=rest, backward=backward)


@dataclass
class TransFileHandler:
    input: Path
    out: Path | None

    def read_input(self) -> list[dict[str, Any]]:
        if self.input.suffix.lower().endswith(".json"):
            text = self.input.read_text(encoding="utf-8")
            obj = json.loads(text)
            return obj["point"]
        raise ValueError

    def write_output(self, result: Sequence[dict[str, Any]]):
        text = json.dumps({"point": result}, ensure_ascii=False, allow_nan=True, separators=(",", ":"))

        if self.out is None:
            sys.stdout.write(text)
        else:
            self.out.parent.mkdir(exist_ok=True, parents=True)
            self.out.touch(exist_ok=True)
            with open(self.out, encoding="utf-8", newline="\n", mode="w") as stream:
                stream.write(text)


class CLI:
    @staticmethod
    def trans(
        toml: str,
        file: Path,
        keys: Sequence[str],
        out: Path | None,
        backward: bool,
    ):
        toml_file = TomlFile(toml)

        keys = list(reversed(keys)) if backward else keys

        file_handler = TransFileHandler(input=file, out=out)
        points = file_handler.read_input()
        points = toml_file.transform(fields=points, keys=keys, backward=backward)
        file_handler.write_output(points)

    @staticmethod
    def add(toml: str, format: FormatType, files: Sequence[str], encoding: str):
        toml_file = TomlFile(toml)

        encoding = encoding or "utf-8"

        adds = []
        for file in files:
            for p in map(Path, glob.glob(file)):
                if p.suffix.lower().endswith(".par"):
                    toml_field = TomlField.from_file(
                        key="U",
                        path=file,
                        format=format,
                        toml=toml,
                        encoding=encoding,
                    )
                elif p.suffix.lower().endswith(".json"):
                    toml_field = TomlField.from_file(
                        key="U",
                        path=file,
                        format=None,
                        toml=toml,
                        encoding=encoding,
                    )
                elif p.suffix.lower().endswith(".csv"):
                    raise ValueError
                else:
                    raise ValueError
                toml_file.append(toml_field)
                adds.append(toml_field)

        toml_file.write()

    @staticmethod
    def remove(
        toml: str,
        keys: Iterable[str],
        regex: bool = False,
    ):
        toml_file = TomlFile(toml)

        chain.from_iterable(toml_file.remove(key, regex=regex) for key in keys)

        toml_file.write()

    @staticmethod
    def list(
        toml: str,
        verbose: int,
    ):
        toml_file = TomlFile(toml)

        text: list = []
        for tag, value in toml_file.items():
            field = TomlField.from_dict(value, toml=toml)
            text.append(field.summary(verbose))

        if text:
            print("".join(text))

    @staticmethod
    def gen(
        files: Sequence[str],
        encoding: str,
        format: str,
    ):
        for file in files:
            for p in map(Path, glob.glob(file)):
                _format = guess_parser(p.stem) if format == "auto" else format

                toml_field = TomlField(
                    key="temp",
                    path=os.fspath(p.absolute()),
                    toml="temp",
                    format=format,
                    encoding=encoding,
                    description=None,
                )

                contents = toml_field.transformer().to_dict()

                # dump
                contents = {
                    "metadata": {
                        "generatedBy": f"{JGDtrans.__cli__} {JGDtrans.__version__}",
                        "originalFormat": toml_field.format,
                        "originalFile": os.fspath(p),
                    },
                    "unit": contents["unit"],
                    "description": contents["description"],
                    "parameter": contents["parameter"],
                }

                text = json.dumps(contents, ensure_ascii=False, allow_nan=True, separators=(",", ":"))

                # write
                path = p.with_suffix(".json")

                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch(exist_ok=True)
                path.write_text(text, encoding="utf-8", newline="\n")


def main():
    parser = argparse.ArgumentParser(
        prog=JGDtrans.__cli__,
        description="Conversion/inversion by parameter which GIAJ publishing",
    )

    parser.add_argument(
        "--version", action="version", version=f"{JGDtrans.__cli__} {JGDtrans.__version__}/Python {sys.version}"
    )

    parser.set_defaults(func=None)
    parser.set_defaults(debug=False)

    sub = parser.add_subparsers(
        title="subcommands",
    )

    #
    # doctor
    #
    # subparser = sub.add_parser(
    #     "doctor",
    #     help="verify registration of files",
    #     description="verify registration of files",
    # )
    # subparser.set_defaults(func=fn_doctor)
    # subparser.add_argument(
    #     "-c",
    #     "--config",
    #     type=Path,
    #     default=Path.home() / pyJGDtrans.__home__ / pyJGDtrans.__config__,
    #     dest="toml",
    #     help=f"{pyJGDtrans.__config__} path (default: %(default)s)",
    # )
    # subparser.add_argument(
    #     "--debug",
    #     action="store_true",
    #     help=f"print detail information",
    # )

    #
    # list
    #
    subparser = sub.add_parser(
        "list",
        help="list registration",
        description="list registration",
        epilog="use doctor to verify the registration",
    )
    subparser.set_defaults(func=CLI.list)
    subparser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path.home() / JGDtrans.__home__ / JGDtrans.__config__,
        dest="toml",
        help=f"{JGDtrans.__config__} path (default: %(default)s)",
    )
    subparser.add_argument("-v", "--verbose", action="count", default=0, help="use verbose output")
    subparser.add_argument("--resolve", action="store_true", help="resolve path and encoding")
    # subparser.add_argument(
    #     "--debug",
    #     action="store_true",
    #     help=f"print detail information",
    # )

    #
    # add
    #
    subparser = sub.add_parser("add", help="register .par file", description="register .par file")
    subparser.set_defaults(func=CLI.add)

    subparser.add_argument(
        "format",
        metavar="FMT",
        choices=["auto"] + list(JGDtrans.parser.PARSER.keys()),
        help="format type of .par file, guess from filename if 'auto' specified: "
        "auto, TKY2JGD, PatchJGD, PatchJGD_H, PatchJGD_HV, HyokoRev, SemiDynaEXE, geonetF3, ITRF2014",
    )
    subparser.add_argument("files", metavar="FILE", nargs="+", type=Path, help=".par/json/csv filename")
    subparser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path.home() / JGDtrans.__home__ / JGDtrans.__config__,
        dest="toml",
        help=f"{JGDtrans.__config__} path (default: %(default)s)",
    )
    subparser.add_argument(
        "--yes",
        "-y",
        action="store_true",
    )
    subparser.add_argument(
        "--encoding",
        "-e",
        default="utf-8",
        help="encoding of the .par file, (default: %(default)s)",
    )
    # subparser.add_argument(
    #     "--debug",
    #     action="store_true",
    #     help=f"print detail information",
    # )

    #
    # remove
    #
    subparser = sub.add_parser("remove", help="unregister .par file", description="unregister .par file")
    subparser.set_defaults(func=CLI.remove)

    subparser.add_argument("tags", metavar="TAG", nargs="+", type=str, help="tag to remove")
    subparser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path.home() / JGDtrans.__home__ / JGDtrans.__config__,
        dest="toml",
        help=f"{JGDtrans.__config__} path (default: %(default)s)",
    )
    subparser.add_argument("-r", "--regex", action="store_true", help="enable regex")
    # subparser.add_argument(
    #     "--debug",
    #     action="store_true",
    #     help=f"print detail information",
    # )

    #
    # trans
    #
    subparser = sub.add_parser("trans", help="transform", description="transform")
    subparser.set_defaults(func=CLI.trans)

    subparser.add_argument(
        "file",
        metavar="FILE",
        type=Path,
        help="filename (json)",
    )
    subparser.add_argument(
        "tags",
        metavar="TAG",
        nargs="+",
        help="tags to use",
    )
    subparser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path.home() / JGDtrans.__home__ / JGDtrans.__config__,
        dest="toml",
        help=f"{JGDtrans.__config__} path (default: %(default)s)",
    )
    subparser.add_argument(
        "-o",
        "--out",
        metavar="OUT",
        default=None,
        type=Path,
        help="filename (json) (default: stdout)",
    )
    subparser.add_argument("-b", "--backward", action="store_true", help="perform backward transformation")
    # subparser.add_argument(
    #     "--debug",
    #     action="store_true",
    #     help=f"print detail information",
    # )

    #
    # gen
    #
    subparser = sub.add_parser(
        "gen", help="generate json file from .par file", description="generate json file (UTF-8) from .par file"
    )
    subparser.set_defaults(func=CLI.gen)

    subparser.add_argument(
        "format",
        metavar="FMT",
        choices=["auto"] + list(JGDtrans.parser.PARSER.keys()),
        help="format of .par file, guess from filename if 'auto' specified: "
        "auto, TKY2JGD, PatchJGD, PatchJGD_H, PatchJGD_HV, HyokoRev, SemiDynaEXE, geonetF3, ITRF2014",
    )
    subparser.add_argument(
        "files",
        metavar="FILE",
        nargs="+",
        type=Path,
        help=".par filename (support glob-like), the resulting file is located in the same directory",
    )
    # subparser.add_argument(
    #     "-m",
    #     "--mode",
    #     metavar="MODE",
    #     choices=["json", "csv"],
    #     default="json",
    #     help="resulting file type: json, csv (default: %(default)s)",
    # )
    subparser.add_argument(
        "-e",
        "--encoding",
        default="utf-8",
        help="encoding of the .par file (default: %(default)s)",
    )
    # subparser.add_argument(
    #     "--debug",
    #     action="store_true",
    #     help=f"print detail information",
    # )

    args = parser.parse_args()

    if args.func is None:
        parser.print_help()
    else:
        args = vars(args)
        del args["debug"]

        func = args.pop("func")
        func(**args)


if __name__ == "__main__":
    main()
