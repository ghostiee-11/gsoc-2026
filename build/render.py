#!/usr/bin/env python3
"""Inject build/data.json into build/page.html and write index.html.

    python3 build/collect.py     # re-read GitHub via the gh CLI, rewrites data.json
    python3 build/render.py      # rebuild index.html from page.html + data.json
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

page = open(os.path.join(HERE, "page.html")).read()
raw = open(os.path.join(HERE, "data.json")).read()
data = json.loads(raw)

out = page.replace("__DATA__", raw.replace("</script>", "<\\/script>"))
if "__DATA__" not in page:
    sys.exit("page.html has no __DATA__ placeholder")
open(os.path.join(ROOT, "index.html"), "w").write(out)

keys = {f'{p["repo"]}#{p["n"]}' for p in data["prs"]}
refs = set()
for m in re.finditer(r'data-prs="([^"]+)"', page):
    refs |= {x.strip() for x in m.group(1).split(",")}
for m in re.finditer(r'data-pr="([^"]+)"', page):
    refs.add(m.group(1).strip())
missing = sorted(refs - keys)

assets = set(re.findall(r'(?:src|href|poster)="(assets/[^"]+)"', page))
disk = {"assets/" + f for f in os.listdir(os.path.join(ROOT, "assets"))}

print(f"index.html  {os.path.getsize(os.path.join(ROOT,'index.html')):,} bytes")
print(f"{len(refs)} pull request references, unresolved: {missing or 'none'}")
print(f"missing assets: {sorted(assets - disk) or 'none'}")
print(f"unused assets: {sorted(disk - assets) or 'none'}")
if missing:
    sys.exit(1)
