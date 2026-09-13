"""Fill Persian translations for a fixed mapping of (file, msgid) -> msgstr.

Parses each po file, matches msgids to the provided dict, writes translated po.
Skips (leaves empty) any msgid not in the dict, so it is safe to run incrementally.
"""
import os
import re
import sys

FA = "/data/workspace/aiorubi/docs/locales/fa/LC_MESSAGES"


def parse_po(path):
    """Return list of blocks: each block = dict with comment lines + msgid lines + msgstr lines."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    blocks = []
    lines = text.split("\n")
    i = 0
    header = []
    # header block = first msgid ""/msgstr multi-line entry
    while i < len(lines):
        if lines[i].startswith("msgid "):
            break
        header.append(lines[i])
        i += 1
    cur = None
    while i < len(lines):
        line = lines[i]
        if line.startswith("#:") or line.startswith("#,") or (line.startswith("#") and not cur):
            blocks.append({"pre": [line], "msgid": [], "msgstr": []})
            i += 1
            continue
        if line.startswith("msgid "):
            if cur is not None:
                blocks.append(cur)
            cur = {"pre": [], "msgid": [line[6:]], "msgstr": []}
            i += 1
            continue
        if line.startswith("msgstr"):
            if cur is not None:
                cur["msgstr"].append(line[6:])
                cur["_in_msgstr"] = True
            i += 1
            continue
        if line.startswith('"'):
            if cur is not None:
                if cur.get("_in_msgstr"):
                    cur["msgstr"].append(line)
                else:
                    cur["msgid"].append(line)
            i += 1
            continue
        if line == "" and cur is not None:
            blocks.append(cur)
            cur = None
        i += 1
    if cur is not None:
        blocks.append(cur)
    return header, blocks


def unquote(po_lines):
    s = "".join(l.strip().strip('"') for l in po_lines)
    s = s.replace('\\"', '"').replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")
    return s


def quote(text):
    """Quote a python string into a single po line."""
    t = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
    return f'"{t}"'


def write_po(path, header, blocks):
    out = []
    out.extend(header)
    for b in blocks:
        out.extend(b["pre"])
        out.append("msgid " + " ".join(f'"{l}"' if not l.startswith('"') else l for l in b["msgid"]) if len(b["msgid"]) == 1 else "msgid \"\"")
        if len(b["msgid"]) > 1:
            for l in b["msgid"][1:] if not b["msgid"][0].startswith('"') else b["msgid"]:
                out.append(f'"{l}"' if not l.startswith('"') else l)
        out.append("msgstr " + b["msgstr"][0] if len(b["msgstr"]) == 1 else "msgstr \"\"")
        if len(b["msgstr"]) > 1:
            for l in b["msgstr"][1:] if not b["msgstr"][0].startswith('"') else b["msgstr"]:
                out.append(f'"{l}"' if not l.startswith('"') else l)
        out.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out).rstrip("\n") + "\n")


def fill(rel, mapping):
    path = os.path.join(FA, rel)
    header, blocks = parse_po(path)
    n = 0
    for b in blocks:
        if not b["msgid"]:
            continue
        key = unquote(b["msgid"])
        if key in mapping and b["msgstr"] and unquote(b["msgstr"]) == "":
            b["msgstr"] = [quote(mapping[key])]
            n += 1
    write_po(path, header, blocks)
    return n


if __name__ == "__main__":
    import json
    job = json.load(open(sys.argv[1], encoding="utf-8"))
    total = 0
    for rel, mapping in job.items():
        c = fill(rel, mapping)
        total += c
        print(f"{rel}: filled {c}")
    print("TOTAL filled:", total)
