# uuid

A tiny, dependency-free CLI tool to print RFC-compliant UUID version 4 and 7 values in several textual formats.

> The script is designed as a small, fast utility you can drop into your shell toolkit and use in scripts, pipelines, or ad‑hoc commands whenever you need fresh UUIDs.

---

## Features

1. UUID v4 (random) and UUID v7 (time-ordered, RFC 9562)
2. Multiple output styles:
    * `hex` (canonical 8-4-4-4-12 with hyphens),
    * `simple` (32 hex digits, no hyphens),
    * `braced` (`{xxxxxxxx-...}`),
    * `urn` (`urn:uuid:...`).
3. Uppercase or lowercase hex
4. Multiple UUIDs per invocation (`-c/--count`)
5. Custom separator (supports `\n`, `\r`, `\t`, `\0`, `\\`)
6. Optional suppression of the final trailing newline (`-n/--no-newline`)

> [!TIP]
> `uuid` is ideal for scripting and templating: 
> you can quickly generate one or many UUIDs in the exact format your tools expect.

---

## Requirements

* Python 3.8+ (system Python is sufficient)
* POSIX-like environment (Linux, macOS, WSL, etc.)

No third‑party Python packages are required!

---

## Installation

Assuming you have cloned or downloaded the repository that contains
`print-uuid.py`.

### 1. Make the script executable

```bash
chmod +x print-uuid.py
```

You can now run it directly:

```bash
./print-uuid.py
```

By default, it prints a single UUID v4 in canonical hex form:

```bash
./print-uuid.py
# e.g. 0c9cf1f8-7a1e-4da2-8a26-1f8531f9b4c5
```

### 2. (Optional) Install as `uuid` on your PATH

If you want a short, convenient command name (`uuid`), 
you can rename or link it into a directory on your `PATH`.

**Option A: rename and move:**

```bash
mv print-uuid.py uuid
chmod +x uuid
sudo mv uuid /usr/local/bin/
```

**Option B: keep the filename and create a symlink:**

```bash
chmod +x /path/to/print-uuid.py
ln -s /path/to/print-uuid.py ~/.local/bin/uuid
```

Make sure `~/.local/bin` is included in your `PATH`.

> [!TIP]
> The script defines the CLI name as `uuid` (via `argparse.ArgumentParser(prog="uuid")`).
> Using `uuid` as the command name will match examples and help output.

---

## Quick start

Assuming the command is available as `uuid`.

### Basic usage

```bash
uuid # prints a UUID v4
uuid 4 # prints a UUID v4 (explicit)
uuid 7 # prints a UUID v7
uuid v7 # same as: uuid 7
```

Example output:

```bash
$ uuid
f3f72236-2c9d-4f8a-9a8a-b10512e8c1fd

$ uuid 7
018f4e6c-5d8b-7c93-8f5b-63b198e03f47
```

### Multiple UUIDs

```bash
uuid 7 -c 5
# prints 5 time-ordered UUID v7 values, one per line
```

### Output formats

```bash
# Canonical hex with hyphens (default)
uuid 7 -f hex

# Simple 32-hex format without hyphens
uuid 7 -f simple

# Braced format
uuid 7 -f braced
# e.g. {018f4e6c-5d8b-7c93-8f5b-63b198e03f47}

# URN format
uuid 7 -f urn
# e.g. urn:uuid:018f4e6c-5d8b-7c93-8f5b-63b198e03f47
```

### Uppercase hex

```bash
uuid 7 --upper
# E.g. 018F4E6C-5D8B-7C93-8F5B-63B198E03F47

uuid 7 -f simple --upper
# E.g. 018F4E6C5D8B7C938F5B63B198E03F47
```

> [!TIP]
> Use `--upper` when your consumer (database, config file, external system)expects uppercase UUIDs.

### Custom separator and no trailing newline

By default, UUIDs are separated by a newline (`\n`), and a final newline is printed at the end.

```bash
uuid 4 -c 3
# uuid1\nuuid2\nuuid3\n
```

You can customize the separator and optionally suppress the final newline:

```bash
# Comma-separated list of 3 UUIDs, no newline at the end
uuid 4 -c 3 -s ',' -n

# NUL-separated UUIDs (useful for low-level tooling)
uuid 4 -c 3 -s '\0' -n

# Windows-style CRLF between UUIDs
uuid 4 -c 2 -s '\r\n'
```

The separator string supports a few backslash escapes:

* `\n` – newline (LF)
* `\r` – carriage return (CR)
* `\t` – horizontal tab
* `\0` – NUL byte
* `\\` – a single backslash

---

## Command-line usage

Basic syntax:

```bash
uuid [version] [OPTIONS]
```

Where `version` is one of:

* `4` or `v4` – UUID v4 (random, RFC 4122)
* `7` or `v7` – UUID v7 (time-ordered, RFC 9562)

If omitted, version `4` is used.

### Options

| Option               | Type       | Default     | Description                                                     |
|----------------------|------------|-------------|-----------------------------------------------------------------|
| `version`            | positional | `4`         | UUID version to generate: `4`, `7`, `v4`, or `v7`.              |
| `-c`, `--count`      | integer    | `1`         | Number of UUIDs to generate. Must be `>= 1`.                    |
| `-f`, `--format`     | `hex`      | `simple`    | `braced`                                                        | `urn` | `hex`       | Output format for UUID strings.                                 |
| `--upper`            | flag       | `False`     | Render hex digits in uppercase.                                 |
| `-s`, `--separator`  | string     | `"\n"` (LF) | Separator between UUIDs; supports `\n`, `\r`, `\t`, `\0`, `\\`. |
| `-n`, `--no-newline` | flag       | `False`     | Do not print the final trailing newline.                        |

> [!IMPORTANT]
> If `--count` is less than 1, `uuid` exits with a usage error and a clear error message.

---

## Implementation notes

### UUID v4

UUID v4 values are generated using Python's built-in `uuid.uuid4()`,
which uses cryptographically strong random numbers from the underlying OS.

### UUID v7

UUID v7 is implemented according to [RFC 9562](https://www.rfc-editor.org/rfc/rfc9562):

* 48-bit Unix timestamp in milliseconds
* Version bits set to `0b0111`
* Variant set to RFC 4122 (binary `10xxxxxx`)
* Remaining bits filled from `os.urandom()`

The resulting UUIDs are time-sortable (their lexicographical order matches creation time),
but strict monotonicity within the same millisecond is not required and not guaranteed.

> [!NOTE]
> This tool focuses on generating RFC-compliant UUIDs quickly and simply.
> It does not implement monotonic UUID v7 sequences or advanced node/clock semantics.

---

## Exit codes

* `0` – success
* `1` – usage error (for example, `--count < 1`)

In case of a usage error, a descriptive message is printed to stderr.

---

## Examples for scripting

### Insert UUID into a config file

```bash
UUID=$(uuid 7 -f simple)
sed -e "s/@UUID@/$UUID/" template.conf > config.conf
```

### Generate N UUIDs for test data

```bash
uuid 4 -c 1000 > uuids.txt
```

### Use NUL-separated UUIDs with other tools

```bash
uuid 4 -c 10 -s '\0' -n > uuids.bin
# now uuids.bin contains 10 NUL-separated UUIDs
```

---

## License & disclaimer

This project is licensed under the [MIT License](./LICENSE).

> [!IMPORTANT]
> While this tool is small and straightforward, it still produces values that may be used in critical systems
> (identifiers, keys, etc.). Make sure it fits your requirements for UUID versions, formats, and randomness before
> using it in production.

---

## Contributing

Issues and pull requests are welcome.
If you would like to propose new flags or behavior, please include concrete examples and a brief rationale
so we can keep `print-uuid` small, understandable, and focused on its core job :innocent:
