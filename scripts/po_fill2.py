"""Persistent fill utility v2: match multiline po blocks, fill empty msgstr from a job json."""
import json
import os
import sys

FA = "/data/workspace/aiorubi/docs/locales/fa/LC_MESSAGES"


def unesc(s):
    return s.replace("\\\\", "\x00").replace('\\"', '"').replace("\\n", "\n").replace("\\t", "\t").replace("\x00", "\\")


def poesc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")


def fill_v2(path, mapping):
    text = open(path, encoding="utf-8").read()
    blocks, cur = [], []
    for line in text.split("\n"):
        if line.strip() == "":
            if cur:
                blocks.append(cur)
            cur = []
        else:
            cur.append(line)
    if cur:
        blocks.append(cur)
    n = 0
    out = []
    for b in blocks:
        if not any(l.startswith(("msgid", "msgstr")) for l in b):
            out.append(b)
            continue
        mid, mstr, mode = [], [], None
        for line in b:
            if line.startswith("msgid"):
                mode = "id"
                rest = line[5:].strip()
                if rest != '""':
                    mid.append(rest[1:-1])
            elif line.startswith("msgstr"):
                mode = "str"
                rest = line[6:].strip()
                if rest != '""':
                    mstr.append(rest[1:-1])
            elif line.startswith('"'):
                (mid if mode == "id" else mstr).append(line.strip()[1:-1])
        content = unesc("".join(mid))
        tr = "".join(mstr)
        if content in mapping and tr == "":
            b_new = [l for l in b if not l.startswith("msgstr")]
            insert_at = max(i for i, l in enumerate(b_new) if l.startswith("msgid")) + 1
            b_new.insert(insert_at, f'msgstr "{poesc(mapping[content])}"')
            out.append(b_new)
            n += 1
        else:
            out.append(b)
    with open(path, "w", encoding="utf-8") as f:
        for b in out:
            f.write("\n".join(b) + "\n\n")
    return n, len([b for b in blocks])


if __name__ == "__main__":
    job = json.load(open(sys.argv[1], encoding="utf-8"))
    total = 0
    unmatched = {}
    for rel, mapping in job.items():
        p = os.path.join(FA, rel)
        if not os.path.exists(p):
            print("MISSING FILE:", rel)
            continue
        c, _ = fill_v2(p, mapping)
        total += c
        print(f"{rel}: filled {c}/{len(mapping)}")
    print("TOTAL filled:", total)
