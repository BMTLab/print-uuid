#!/usr/bin/python3
"""
Name: print-uuid.py
Author: Nikita Neverov (BMTLab)
Version: 1.0.0
Date: 2025-11-21
License: MIT

Description
-----------
Tiny CLI to print RFC-compliant UUID v4 or v7 in various textual formats.

Features
--------
- UUID v4 (random) and UUID v7 (time-ordered, RFC 9562).
- Configurable output format: hex, simple, braced, URN.
- Uppercase or lowercase hex.
- Multiple UUIDs per invocation.
- Custom separator and optional trailing newline suppression.

Usage
-----
Basic usage::

    uuid            # prints a UUID v4
    uuid 4          # prints a UUID v4
    uuid 7          # prints a UUID v7

Formatting and count::

    uuid 7 -c 5                 # print 5 UUID v7
    uuid 7 -f urn               # URN format (urn:uuid:...)
    uuid 7 --upper              # uppercase hex
    uuid 7 --separator '\\n' -c 3
    uuid v7 -f simple --upper   # 32 uppercase hex chars without dashes

Options
-------
- ``uuid [version]``      - version is ``4``, ``7``, ``v4`` or ``v7`` (default: ``4``).
- ``-c, --count N``       - number of UUIDs to generate (default: ``1``).
- ``-f, --format FMT``    - one of ``hex``, ``simple``, ``braced``, ``urn`` (default: ``hex``).
- ``--upper``             - render hex digits in uppercase.
- ``-s, --separator SEP`` - separator between UUIDs; supports ``\\n``, ``\\r``, ``\\t``, ``\\0``.
- ``-n, --no-newline``    - do not print a final trailing newline.

Exit codes
----------
0  Success.
1  Usage error (for example, invalid ``--count``).
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import uuid
from collections.abc import Sequence
from typing import Any

EXIT_OK: int = 0
EXIT_USAGE: int = 1

DEFAULT_SEPARATOR_LITERAL: str = r"\n"

# Precomputed constants for UUID v7 bit operations
_UUID7_TS_MASK: int = (1 << 48) - 1
_UUID7_RAND_A_MASK: int = 0x0FFF
_UUID7_VERSION: int = 0x7
_UUID7_VERSION_SHIFT: int = 12
_UUID7_VARIANT_CLEAR_MASK: int = 0x3F
_UUID7_VARIANT_SET_BITS: int = 0x80
_UUID7_TS_BYTES_LEN: int = 6
_UUID7_RAND_A_BYTES_LEN: int = 2
_UUID7_RAND_B_BYTES_LEN: int = 8


def eprint(*args: Any) -> None:
    """Print the given arguments to stderr."""
    # noinspection PyTypeChecker
    print(*args, file=sys.stderr)


def uuid7() -> uuid.UUID:
    """Generate an RFC 9562 UUID version 7.

    Layout (big-endian)
    -------------------
    - 48 bits: Unix timestamp in milliseconds
    - 4  bits: version (0b0111)
    - 12 bits: rand_a
    - 2  bits: variant (RFC 4122 -> 0b10)
    - 62 bits: rand_b

    Implementation details
    ----------------------
    - Uses :func:`os.urandom` for entropy.
    - Correctly sets version and variant bits.
    - Values are time-sortable;
      strict monotonicity within the same millisecond is not guaranteed
      and is not required by the specification.

    Returns
    -------
    uuid.UUID
        A freshly generated version 7 UUID.
    """
    # Bind functions locally to avoid repeated global lookups in tight loops
    time_ns = time.time_ns
    urandom = os.urandom

    # 48-bit timestamp (Unix epoch milliseconds)
    ts_ms: int = (time_ns() // 1_000_000) & _UUID7_TS_MASK
    ts_bytes: bytes = ts_ms.to_bytes(_UUID7_TS_BYTES_LEN, byteorder="big")

    # 12 random bits for rand_a; top 4 bits = version (0b0111)
    rand_a: int = int.from_bytes(
        urandom(_UUID7_RAND_A_BYTES_LEN),
        byteorder="big",
    ) & _UUID7_RAND_A_MASK
    ver_and_rand_a: bytes = (
            (_UUID7_VERSION << _UUID7_VERSION_SHIFT) | rand_a
    ).to_bytes(_UUID7_RAND_A_BYTES_LEN, byteorder="big")

    # 62 random bits for rand_b across the last 8 bytes; set variant to 10xxxxxx
    tail_bytes: bytearray = bytearray(urandom(_UUID7_RAND_B_BYTES_LEN))
    tail_bytes[0] = (tail_bytes[0] & _UUID7_VARIANT_CLEAR_MASK) | _UUID7_VARIANT_SET_BITS

    raw: bytes = ts_bytes + ver_and_rand_a + tail_bytes

    return uuid.UUID(bytes=raw)


def format_uuid(
        u: uuid.UUID,
        style: str = "hex",
        upper: bool = False
) -> str:
    """Format a UUID in one of the supported textual styles.

    Parameters
    ----------
    u : uuid.UUID
        UUID object to format.
    style : {'hex', 'simple', 'braced', 'urn'}, optional
        Output style:

        - ``"hex"``    – canonical 8-4-4-4-12 with hyphens (default).
        - ``"simple"`` – 32 hex digits without hyphens.
        - ``"braced"`` – ``"{xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}"``.
        - ``"urn"``    – ``"urn:uuid:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"``.
    upper : bool, optional
        If ``True``, convert hex digits to uppercase.

    Returns
    -------
    str
        Formatted UUID string.

    Raises
    ------
    ValueError
        If an unknown format style is requested.
    """
    # Compute canonical string only once where it is needed
    if style == "hex":
        text: str = str(u)
    elif style == "simple":
        text = u.hex
    elif style == "braced":
        canonical: str = str(u)
        text = "{" + canonical + "}"
    elif style == "urn":
        # ``u.urn`` already contains "urn:uuid:..."
        text = u.urn
    else:
        raise ValueError(f"Unknown format: {style!r}")

    return text.upper() if upper else text


def unescape_separator(raw: str) -> str:
    """Interpret common backslash escapes in a separator string.

    Supported escape sequences
    --------------------------
    - ``"\\n"`` → newline (LF)
    - ``"\\r"`` → carriage return (CR)
    - ``"\\t"`` → horizontal tab (TAB)
    - ``"\\0"`` → NUL byte
    - ``"\\\\"`` → a single backslash

    Parameters
    ----------
    raw : str
        Raw separator as passed on the command line.

    Returns
    -------
    str
        Separator with escape sequences interpreted.
    """
    return (
        raw.replace("\\n", "\n")
        .replace("\\r", "\r")
        .replace("\\t", "\t")
        .replace("\\0", "\x00")
        .replace("\\\\", "\\")
    )


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse command-line arguments for the UUID CLI.

    Parameters
    ----------
    argv : Sequence[str]
        Argument vector, usually ``sys.argv[1:]``.

    Returns
    -------
    argparse.Namespace
        Parsed arguments namespace.

    Raises
    ------
    SystemExit
        If validation fails (for example, ``--count < 1``).
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="uuid",
        description="Print a UUID v4 (random) or v7 (time-ordered).",
    )
    parser.add_argument(
        "version",
        nargs="?",
        choices=("4", "7", "v4", "v7"),
        default="4",
        help="UUID version to generate (4, 7, v4, v7). Default: 4.",
    )
    parser.add_argument(
        "-c",
        "--count",
        type=int,
        default=1,
        help="How many UUIDs to print (default: 1). Must be >= 1.",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=("hex", "simple", "braced", "urn"),
        default="hex",
        help="Output format (default: hex).",
    )
    parser.add_argument(
        "--upper",
        action="store_true",
        help="Use uppercase hex.",
    )
    parser.add_argument(
        "-s",
        "--separator",
        default=DEFAULT_SEPARATOR_LITERAL,
        help=(
            r"Separator between UUIDs. Supports \n, \r, \t, \0, \\; "
            r"default: '\n'."
        ),
    )
    parser.add_argument(
        "-n",
        "--no-newline",
        action="store_true",
        help="Do not print the final trailing newline (useful for scripting).",
    )

    args: argparse.Namespace = parser.parse_args(argv)

    if args.count < 1:
        # Treat invalid count as a usage error with a deterministic exit code
        eprint("ERROR: --count must be >= 1")
        raise SystemExit(EXIT_USAGE)

    # Normalize version to "4" or "7" internally
    version_raw: str = args.version
    if version_raw in ("v4", "V4"):
        args.version = "4"
    elif version_raw in ("v7", "V7"):
        args.version = "7"

    # Interpret escapes in separator once
    args.separator = unescape_separator(args.separator)

    return args


def generate_uuid_strings(
        count: int,
        version: str,
        fmt: str,
        upper: bool,
) -> list[str]:
    """Generate a list of formatted UUID strings.

    Parameters
    ----------
    count : int
        Number of UUIDs to generate. Must be >= 1.
    version : {'4', '7'}
        UUID version identifier.
    fmt : {'hex', 'simple', 'braced', 'urn'}
        Output format for each UUID.
    upper : bool
        If ``True``, emit uppercase hex.

    Returns
    -------
    list[str]
        List of formatted UUID strings.
    """
    # Select generator and formatter once, then reuse in the loop
    generator = uuid.uuid4 if version == "4" else uuid7
    formatter = format_uuid

    return [
        formatter(generator(), style=fmt, upper=upper)
        for _ in range(count)
    ]


def main(argv: Sequence[str] | None = None) -> int:
    """Run the UUID CLI.

    Parameters
    ----------
    argv : Sequence[str] or None, optional
        Command-line arguments excluding the program name.
        If ``None``, ``sys.argv[1:]`` is used.

    Returns
    -------
    int
        Exit status code. ``0`` on success, non-zero on error.
    """
    if argv is None:
        argv = sys.argv[1:]

    args: argparse.Namespace = parse_args(argv)

    # Generate UUIDs as formatted strings
    values: list[str] = generate_uuid_strings(
        count=args.count,
        version=args.version,
        fmt=args.format,
        upper=args.upper,
    )

    payload: str = args.separator.join(values)

    if args.no_newline:
        sys.stdout.write(payload)
    else:
        sys.stdout.write(payload + "\n")

    sys.stdout.flush()

    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
### End
