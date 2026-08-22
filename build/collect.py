#!/usr/bin/env python3
"""Read every pull request and issue by one GitHub user across the project's
repositories and write build/data.json, which build/render.py inlines into the page.

    python3 build/collect.py            # refresh from GitHub
    python3 build/render.py             # rebuild index.html

Requires the `gh` CLI, authenticated. Set GH=/path/to/gh if it is not on PATH.
"""
import collections
import datetime
import json
import os
import shutil
import subprocess
import sys

USER = "ghostiee-11"
GH = os.environ.get("GH") or shutil.which("gh") or os.path.expanduser("~/bin/gh")
HERE = os.path.dirname(os.path.abspath(__file__))

PR_REPOS = [
    "holoviz/lumen", "holoviz/panel", "holoviz/holoviews", "holoviz/hvplot",
    "holoviz/param", "holoviz/holoviz", "holoviz-dev/blog", "holoviz-dev/holoviz-skills",
    "xqlsystems/xarray-sql", "narwhals-dev/narwhals", "bokeh/bokeh", "pydata/xarray",
    "python/cpython", "jupyter-widgets/ipywidgets", "stac-utils/xpystac",
    "panel-extensions/panel-material-ui", "panel-extensions/panel-live-server",
    "numfocus/gsoc", "vinta/awesome-python", "academic/awesome-datascience",
    "holoviz-topics/lumen-ourworldindata",
]
ISSUE_REPOS = [
    "holoviz/lumen", "holoviz/panel", "holoviz/holoviews", "xqlsystems/xarray-sql",
    "narwhals-dev/narwhals", "bokeh/bokeh", "stac-utils/xpystac",
    "panel-extensions/panel-material-ui", "holoviz-topics/lumen-ourworldindata",
]

# A pull request belongs to the workstream that claims it; "<repo>#*" claims a whole repo.
WORKSTREAMS = {
    "source":   ["holoviz/lumen#1741", "holoviz/lumen#1791", "holoviz/lumen#1886",
                 "holoviz/lumen#1908", "holoviz/lumen#1926", "holoviz/lumen#1756"],
    "gridded":  ["holoviz/lumen#1823", "holoviz/lumen#1943", "holoviz/lumen#1944",
                 "holoviz/lumen#2049", "holoviz/lumen#1824", "holoviz/lumen#1825",
                 "holoviz/lumen#1783", "holoviz/lumen#1934", "holoviz/lumen#1933",
                 "holoviz/lumen#1936", "holoviz/lumen#1927", "holoviz/lumen#1929"],
    "upstream": ["xqlsystems/xarray-sql#*"],
    "narwhals": ["holoviz/lumen#2008", "holoviz/lumen#2039", "holoviz/lumen#2044",
                 "holoviz/lumen#2046", "holoviz/lumen#2050", "holoviz/lumen#2051",
                 "narwhals-dev/narwhals#*", "holoviz/param#*"],
    "filters":  ["holoviz/lumen#1894", "holoviz/lumen#1779"],
    "geo":      ["holoviz/lumen#1903", "holoviz/lumen#1905", "holoviz/lumen#1996",
                 "holoviz/lumen#1998", "holoviz/lumen#1999", "holoviz/lumen#2001",
                 "holoviz/lumen#1997", "holoviz/lumen#1995", "holoviz/lumen#1993",
                 "holoviz/lumen#1725", "holoviz/panel#8664", "holoviz/panel#8521"],
    "catalog":  ["holoviz/lumen#1867", "holoviz/lumen#1889", "stac-utils/xpystac#*"],
    "owid":     ["holoviz-topics/lumen-ourworldindata#*"],
}
WS_ORDER = ["source", "upstream", "gridded", "filters", "geo", "narwhals",
            "catalog", "owid", "lumen-core", "ecosystem"]
CORE_REPOS = {"holoviz/lumen", "xqlsystems/xarray-sql", "narwhals-dev/narwhals",
              "stac-utils/xpystac", "holoviz/param", "holoviz/panel",
              "holoviz/holoviews", "holoviz/hvplot",
              "holoviz-topics/lumen-ourworldindata"}

WEEK0 = datetime.date(2026, 3, 2)     # Monday of the week the first pull request opened
WEEK_LAST = datetime.date(2026, 8, 24)

claim = {}
for ws, keys in WORKSTREAMS.items():
    for k in keys:
        claim[k] = ws


def gh(*args):
    r = subprocess.run([GH, *args], capture_output=True, text=True)
    if r.returncode:
        print(f"  ! {' '.join(args[:4])}: {r.stderr.strip().splitlines()[:1]}", file=sys.stderr)
        return []
    return json.loads(r.stdout or "[]")


rows = []
for repo in PR_REPOS:
    got = gh("pr", "list", "--repo", repo, "--author", USER, "--state", "all",
             "--limit", "300", "--json",
             "number,title,state,url,createdAt,mergedAt,additions,deletions,changedFiles,isDraft")
    print(f"{repo:42s} {len(got):3d} pull requests")
    for p in got:
        key = f"{repo}#{p['number']}"
        ws = claim.get(key) or claim.get(f"{repo}#*")
        if p["mergedAt"]:
            state = "merged"
        elif p["state"] == "OPEN":
            state = "draft" if p["isDraft"] else "open"
        else:
            state = "closed"
        core = bool(ws) or repo in CORE_REPOS
        rows.append({
            "kind": "pr", "repo": repo, "n": p["number"], "t": p["title"],
            "s": state, "u": p["url"],
            "d": (p["mergedAt"] or p["createdAt"])[:10], "created": p["createdAt"][:10],
            "add": p["additions"], "del": p["deletions"], "f": p["changedFiles"],
            "ws": ws or ("lumen-core" if core else "ecosystem"), "core": core,
        })

issues = []
for repo in ISSUE_REPOS:
    got = gh("issue", "list", "--repo", repo, "--author", USER, "--state", "all",
             "--limit", "300", "--json", "number,title,state,url,createdAt,closedAt")
    print(f"{repo:42s} {len(got):3d} issues")
    for p in got:
        issues.append({"kind": "issue", "repo": repo, "n": p["number"], "t": p["title"],
                       "s": "closed" if p["state"] == "CLOSED" else "open",
                       "u": p["url"], "d": p["createdAt"][:10]})

if not rows:
    sys.exit("no pull requests returned; check `gh auth status`")

rows.sort(key=lambda r: (r["d"], r["repo"], r["n"]))
issues.sort(key=lambda r: (r["d"], r["repo"], r["n"]))

weeks, cur = [], WEEK0
while cur <= WEEK_LAST:
    weeks.append(cur.isoformat())
    cur += datetime.timedelta(days=7)

cells = collections.defaultdict(lambda: {"n": 0, "m": 0, "add": 0, "prs": []})
for r in rows:
    i = (datetime.date.fromisoformat(r["d"]) - WEEK0).days // 7
    if not 0 <= i < len(weeks):
        continue
    c = cells[(i, r["ws"])]
    c["n"] += 1
    if r["s"] == "merged":
        c["m"] += 1
        c["add"] += r["add"]
    c["prs"].append(f'#{r["n"]} {r["t"][:58]}')

raster = [{"w": i, "ws": w, "n": v["n"], "m": v["m"], "add": v["add"], "prs": v["prs"]}
          for (i, w), v in sorted(cells.items(), key=lambda kv: (kv[0][0], WS_ORDER.index(kv[0][1])))]


def tally(sel):
    t = collections.Counter()
    ma = md = mf = aa = ad = 0
    for r in sel:
        t[r["s"]] += 1
        aa += r["add"]
        ad += r["del"]
        if r["s"] == "merged":
            ma += r["add"]; md += r["del"]; mf += r["f"]
    return {"total": len(sel), **t, "merged_add": ma, "merged_del": md,
            "merged_files": mf, "all_add": aa, "all_del": ad}


def where(fn):
    return tally([r for r in rows if fn(r)])


stats = {
    "all": tally(rows),
    "holoviz": where(lambda r: r["repo"].startswith("holoviz")),
    "upstream": where(lambda r: not r["repo"].startswith("holoviz")),
    "core": where(lambda r: r["core"]),
    "lumen": where(lambda r: r["repo"] == "holoviz/lumen"),
    "xarray_sql": where(lambda r: r["repo"] == "xqlsystems/xarray-sql"),
    "issues": len(issues),
    "issues_closed": sum(1 for i in issues if i["s"] == "closed"),
    "repos": len({r["repo"] for r in rows}),
    "first": rows[0]["created"],
    "last": max(r["d"] for r in rows),
}
by_ws = {w: where(lambda r, w=w: r["ws"] == w) for w in WS_ORDER}

out = {"prs": rows, "issues": issues, "weeks": weeks, "raster": raster,
       "wsOrder": WS_ORDER, "stats": stats, "by_ws": by_ws}
path = os.path.join(HERE, "data.json")
json.dump(out, open(path, "w"), separators=(",", ":"))

print(f"\n{stats['all']['total']} pull requests, {stats['all']['merged']} merged, "
      f"{stats['repos']} repositories, {stats['issues']} issues")
print(f"{stats['first']} to {stats['last']} · {len(weeks)} weeks · {len(raster)} field cells")
print(f"wrote {path} ({os.path.getsize(path):,} bytes)")
