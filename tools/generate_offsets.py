#!/usr/bin/env python3
"""Regenerates csgo_sdk/offsets.h from offsets.cs (hazedumper dump).

Usage:
    python tools/generate_offsets.py [--source offsets.cs] [--output csgo_sdk/offsets.h]

Drop a fresh offsets.cs from https://github.com/frk1/hazedumper next to the repo
root and re-run this script, the header is overwritten from scratch.
"""

import argparse
import os
import re
import sys

CONST_RE = re.compile(r"public const Int32 (\w+) = (0x[0-9A-Fa-f]+);")
CLASS_RE = re.compile(r"public static class (\w+)\s*\{(.*?)\n[ \t]*\}", re.S)
DUMP_DATE_RE = re.compile(r"//\s*(\d{4}-\d{2}-\d{2}[ T][0-9:. ]*UTC)")
TIMESTAMP_RE = re.compile(r"public const Int32 timestamp = (\d+);")

# Offsets hazedumper does not dump, kept by hand.
EXTRA = {
    "netvars": {
        "m_iIndex": 0x64,
    },
}

HEADER = """\
#pragma once
//
// GENERATED FILE - DO NOT EDIT BY HAND
// Regenerate it with:  python tools/generate_offsets.py
//
// Source dump : offsets.cs (hazedumper), {dump_date}
// Timestamp   : {timestamp}
//
// Every offset is relative to the base of the module it lives in, see
// sdk::modules_t for the module bases. csgo.exe is a 32 bit process, so build
// this project as x86 (Win32) - see README.md.
//
#include <cstddef>
#include <cstdint>

namespace sdk {{
"""

NAMESPACE_HEADER = """\
\t// {description}
\tnamespace {name} {{
"""

FOOTER = """
} // namespace sdk
"""


def parse(path):
    with open(path, "r", encoding="utf-8-sig") as handle:
        source = handle.read().replace("\r\n", "\n")

    dump_match = DUMP_DATE_RE.search(source)
    stamp_match = TIMESTAMP_RE.search(source)

    classes = {}
    for name, body in CLASS_RE.findall(source):
        offsets = {key: int(value, 16) for key, value in CONST_RE.findall(body)}
        for extra_key, extra_value in EXTRA.get(name, {}).items():
            offsets[extra_key] = extra_value
        classes[name] = offsets

    if not classes:
        sys.exit("error: no 'public static class' blocks found in %s" % path)

    return {
        "dump_date": dump_match.group(1).strip() if dump_match else "unknown",
        "timestamp": stamp_match.group(1) if stamp_match else "unknown",
        "classes": classes,
    }


def render(dump):
    descriptions = {
        "netvars": "Netvars, relative to an entity (see sdk::entity_t).",
        "signatures": "Signatures / RVA offsets, relative to a module base.",
    }

    namespaces = []

    for name in sorted(dump["classes"]):
        offsets = dump["classes"][name]
        # Signatures are added to a module base, netvars to an entity pointer.
        value_type = "std::uintptr_t" if name == "signatures" else "std::ptrdiff_t"

        block = [NAMESPACE_HEADER.format(
            description=descriptions.get(name, "Offsets."),
            name=name,
        )]

        for key in sorted(offsets):
            note = "  //not dumped by hazedumper" if key in EXTRA.get(name, {}) else ""
            block.append("\t\tconstexpr %s %s = 0x%X;%s\n" % (value_type, key, offsets[key], note))

        block.append("\t}\n")
        namespaces.append("".join(block))

    return (
        HEADER.format(dump_date=dump["dump_date"], timestamp=dump["timestamp"])
        + "\n".join(namespaces)
        + FOOTER
    )


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=os.path.join(root, "offsets.cs"))
    parser.add_argument("--output", default=os.path.join(root, "csgo_sdk", "offsets.h"))
    args = parser.parse_args()

    dump = parse(args.source)
    text = render(dump)

    with open(args.output, "w", encoding="utf-8", newline="\r\n") as handle:
        handle.write(text)

    total = sum(len(offsets) for offsets in dump["classes"].values())
    print("wrote %s (%d offsets from %s)" % (args.output, total, args.source))


if __name__ == "__main__":
    main()
