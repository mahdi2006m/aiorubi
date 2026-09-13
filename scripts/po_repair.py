"""Repair po files where the translated msgstr landed before the msgid continuation lines.
Canonical repair: rebuild each entry block so order is: comments, msgid (multiline), msgstr (single line)."""
import glob
import subprocess

FA = "/data/workspace/aiorubi/docs/locales/fa/LC_MESSAGES"


def unesc(s):
    return s.replace("\\\\", "\x00").replace('\\"', '"').replace("\\n", "\n").replace("\\t", "\t").replace("\x00", "\\")


def poesc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")


def repair(path):
    text = open(path, encoding="utf-8").read()
    # separate header (first blank-line-terminated block starting msgid "")
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
    header_blocks = []
    entries = []
    for b in blocks:
        if b and b[0].startswith("msgid") and not any(l.startswith("#") for l in b):
            header_blocks.append(b)
        else:
            entries.append(b)
    out = []
    # header first (as-is)
    for hb in header_blocks:
        out.append(hb)
    for b in entries:
        pre = [l for l in b if l.startswith("#")]
        body = [l for l in b if not l.startswith("#")]
        mid, mstr = [], []
        mode = None
        str_i = None
        for i, line in enumerate(body):
            if line.startswith("msgid"):
                mode = "id"
                rest = line[5:].strip()
                if rest != '""':
                    mid.append(rest[1:-1])
            elif line.startswith("msgstr"):
                if str_i is None:
                    str_i = i
                mode = "str"
                rest = line[6:].strip()
                if rest != '""':
                    mstr.append(rest[1:-1])
            elif line.startswith('"'):
                if mode == "id" or str_i is None:
                    mid.append(line.strip()[1:-1])
                else:
                    mstr.append(line.strip()[1:-1])
        content = unesc("".join(mid))
        tr = "".join(mstr)
        if not content:
            continue
        out.append(pre + [f'msgid "{poesc(content)}"', f'msgstr "{poesc(tr)}"'])
    with open(path, "w", encoding="utf-8") as f:
        first = True
        for b in out:
            f.write("\n".join(b) + "\n\n")
    return len(entries)


fails = 0
for p in sorted(glob.glob(f"{FA}/**/*.po", recursive=True)):
    repair(p)
    r = subprocess.run(["msgfmt", "--check", "--statistics", p, "-o", "/dev/null"], capture_output=True, text=True)
    if r.returncode != 0:
        fails += 1
        print("FAIL", p.split("LC_MESSAGES/")[1], "|", r.stderr.strip().splitlines()[0][:100])
print("repair done | failing:", fails)
